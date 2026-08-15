import { useRef, useState } from 'react';

interface VideoDropzoneProps {
  onFileSelected: (file: File) => void;
}

export function VideoDropzone({ onFileSelected }: VideoDropzoneProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragOver, setDragOver] = useState(false);

  const openPicker = () => inputRef.current?.click();

  return (
    <div
      className="dropzone"
      data-dragover={dragOver}
      role="button"
      tabIndex={0}
      onClick={openPicker}
      onKeyDown={e => { if (e.key === 'Enter' || e.key === ' ') openPicker(); }}
      onDragOver={e => { e.preventDefault(); setDragOver(true); }}
      onDragLeave={e => { e.preventDefault(); setDragOver(false); }}
      onDrop={e => {
        e.preventDefault();
        setDragOver(false);
        const file = e.dataTransfer.files?.[0];
        if (file) onFileSelected(file);
      }}
    >
      <div className="dropzone-icon">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="var(--color-accent-700)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M12 16V4M12 4l-5 5M12 4l5 5" />
          <path d="M4 18v2a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-2" />
        </svg>
      </div>
      <p className="dropzone-title">Drop a video here, or click to browse</p>
      <p className="text-muted dropzone-sub">MP4, MOV or WebM - up to 500MB</p>
      <input
        ref={inputRef}
        type="file"
        accept="video/*"
        data-testid="file-input"
        style={{ display: 'none' }}
        onChange={e => {
          const file = e.target.files?.[0];
          if (file) onFileSelected(file);
        }}
      />
    </div>
  );
}
