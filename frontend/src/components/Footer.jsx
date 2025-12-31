import React from 'react'

// Footer with contact and GitHub link
export default function Footer(){
  return (
    <footer className="mt-12 bg-slate-50 border-t border-slate-100">
      <div className="container mx-auto px-4 py-8 flex flex-col md:flex-row justify-between items-center gap-4">
        <div className="text-sm text-slate-600">© 2025 AI Parser — Built for students, jobseekers & recruiters.</div>
        <div className="flex items-center gap-4">
          <a href="#contact" className="text-slate-600 hover:text-primary">Contact</a>
          <a href="https://github.com/" target="_blank" rel="noreferrer" className="text-slate-600 hover:text-primary">GitHub</a>
        </div>
      </div>
    </footer>
  )
}
