import React from 'react'

export default function Hero(){
  return (
    <section className="hero-modern">
      <div className="hero-grid container-custom">
        <div className="hero-left">
          <div className="tagline">Smart hiring, faster.</div>
          <h1 className="hero-title">Find the best talent with ThinkHire</h1>
          <p className="hero-subtitle">AI-powered candidate screening and intelligent matching that helps recruiters shortlist quality candidates faster — without the manual heavy-lifting.</p>

          <div className="hero-ctas">
            <a href="/login" className="btn-primary">Get Started</a>
            <a href="#about" className="btn-ghost">How it Works</a>
          </div>
        </div>

        <div className="hero-right">
          <div className="hero-shape" aria-hidden="true" />
          <img src="/static/images/team-illustration.png" alt="Team" className="hero-illustration" />
          <div className="floating-card">We Have Awesome Team</div>
        </div>
      </div>
    </section>
  )
}
