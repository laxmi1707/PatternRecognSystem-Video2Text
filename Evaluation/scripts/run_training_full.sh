#!/usr/bin/env bash
# The training that runs once the frame cache is complete.
#
# Four stages, cheapest first, so a useful number exists even if a later stage
# has to be stopped:
#
#   A  every one of the 14 models, on a sample of recordings   -> which model
#   B  every model, one row per recording, all of them         -> the labels'
#                                                                 own granularity
#   C  one block at a time, one row per recording              -> which features
#   D  the models that scale, one row per segment, all of them -> the backend's
#                                                                 granularity
#
# B is cheap - one row per recording is ~7k rows against ~40k segments - and it
# is the comparison the report needs: the labels are per recording, so a
# segment-level model is asked to call a password prompt `run_command` because
# the recording around it was one.
#
# Stage A is sampled because the quadratic models grow badly: measured on 1443
# segments (run_005), SVM fits in 1.0 s and voting in 3.3 s, which extrapolates
# to roughly 13 and 42 minutes per fold at 32k training rows - affordable once,
# not while picking between 14 models and 3 feature sets. Sampling is by
# recording, so folds stay task-grouped and the numbers stay honest; the report
# records the sample size next to the score.
#
# Start:  nohup bash run_training_full.sh > logs/training_full.log 2>&1 &

cd "$(dirname "$0")"
PY=.venv/Scripts/python.exe
LABELS=csv:labels/labels_v2.csv
STATUS=logs/training.status
THREADS=${V2K_TRAIN_THREADS:-12}

say() { echo "$(date '+%F %T') $*" | tee -a "$STATUS"; }

# Everything but stacking and late_fusion, which are three fits each for scores
# run_005 showed voting already reaching. They stay in stage A for the record.
FULL="svm naive_bayes decision_tree random_forest knn xgboost lightgbm mlp cnn1d lstm transformer voting"

say "stage A: all 14 models on a 2500-recording sample"
"$PY" -m v2k train --labels "$LABELS" \
    --features native150 cnn native150+cnn \
    --models all --folds 5 --min-tasks 10 --sample-tasks 2500 \
    --threads "$THREADS" --name "v2-full-modelpick" >> logs/train_full_A.log 2>&1
say "stage A exited $?"

say "stage B: all 14 models, one row per recording, every recording"
"$PY" -m v2k train --labels "$LABELS" \
    --features native150 cnn native150+cnn \
    --models all --folds 5 --min-tasks 10 --level task \
    --threads "$THREADS" --save-all --name "v2-full-tasklevel" >> logs/train_full_B.log 2>&1
say "stage B exited $?"

say "stage C: one feature block at a time"
"$PY" -m v2k train --labels "$LABELS" \
    --features ocr_native ui visual interaction cnn \
    --models random_forest lightgbm mlp --folds 5 --min-tasks 10 --level task \
    --threads "$THREADS" --name "v2-full-ablation" >> logs/train_full_C.log 2>&1
say "stage C exited $?"

# Last because it is the most expensive by far - ~40k rows, and SVM and voting
# are quadratic in them - and because it measures the granularity the labels do
# not have. If it has to be cut for time, A, B and C still carry the report.
say "stage D: one row per segment, every recording"
"$PY" -m v2k train --labels "$LABELS" \
    --features native150 native150+cnn \
    --models $FULL --folds 5 --min-tasks 10 \
    --threads "$THREADS" --save-all --name "v2-full-segment" >> logs/train_full_D.log 2>&1
say "stage D exited $?"

say "training finished - see runs/"
