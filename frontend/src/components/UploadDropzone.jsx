import React, {useState, useRef} from 'react'

// UploadDropzone: minimal drag-and-drop UI that accepts PDF/DOCX
// This component is standalone and can be wired to an API endpoint.
export default function UploadDropzone(){
  const [fileName, setFileName] = useState(null)
  const inputRef = useRef()

  function handleFiles(files){
    const f = files?.[0]
    if(!f) return
    setFileName(f.name)
    // TODO: perform upload to backend here (fetch/post)
  }

  return (
    <div>
      <label htmlFor="file" className="dropzone block cursor-pointer">
        <input ref={inputRef} id="file" type="file" accept=".pdf,.docx" className="hidden" onChange={(e)=>handleFiles(e.target.files)} />
        <div className="flex flex-col items-center justify-center gap-2">
          <svg xmlns="http://www.w3.org/2000/svg" className="h-10 w-10 text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7 16l5-5 5 5" />
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 3v12" />
          </svg>
          <div className="text-sm text-slate-600">Drop your resume here or click to browse</div>
          <div className="mt-2">
            <button type="button" onClick={()=>inputRef.current.click()} className="btn-primary">Choose File</button>
          </div>
        </div>
      </label>

      {fileName && (
        <div className="mt-3 text-sm text-slate-700">Selected: <strong>{fileName}</strong></div>
      )}
    </div>
  )
}
