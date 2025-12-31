import React from 'react'

// Steps: visually explain the flow Upload -> Analyze -> Results
export default function Steps(){
  const steps = [
    {title: 'Upload', desc: 'Add your resume (PDF/DOCX) or drag & drop.'},
    {title: 'Analyze', desc: 'NLP-powered parsing and skill extraction.'},
    {title: 'Get Results', desc: 'View matched roles, scores and suggestions.'}
  ]

  return (
    <div className="flex flex-col gap-4">
      {steps.map((s, i)=> (
        <div key={i} className="flex items-start gap-4">
          <div className="min-w-[40px] h-[40px] rounded-full bg-primary/10 text-primary flex items-center justify-center font-semibold">{i+1}</div>
          <div>
            <div className="font-semibold">{s.title}</div>
            <div className="text-sm text-slate-600">{s.desc}</div>
          </div>
        </div>
      ))}
    </div>
  )
}
