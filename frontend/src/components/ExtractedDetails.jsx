import React from 'react'

// ExtractedDetails: example preview of parsed fields. In a real app this would be populated from backend response.
export default function ExtractedDetails(){
  const sample = {
    name: 'Ananya Sharma',
    skills: ['Python', 'NLP', 'Machine Learning', 'SQL'],
    education: 'B.Tech, Computer Science, IIT Example (2020)',
    experience: '2 years — Software Engineer at ExampleCorp'
  }

  return (
    <div className="grid gap-4 md:grid-cols-2">
      <div>
        <div className="text-sm text-slate-500">Name</div>
        <div className="font-medium">{sample.name}</div>
      </div>

      <div>
        <div className="text-sm text-slate-500">Skills</div>
        <div className="flex flex-wrap gap-2 mt-2">
          {sample.skills.map((s, i)=> (
            <span key={i} className="text-sm bg-primary/10 text-primary px-3 py-1 rounded-full">{s}</span>
          ))}
        </div>
      </div>

      <div>
        <div className="text-sm text-slate-500">Education</div>
        <div className="font-medium">{sample.education}</div>
      </div>

      <div>
        <div className="text-sm text-slate-500">Experience</div>
        <div className="font-medium">{sample.experience}</div>
      </div>
    </div>
  )
}
