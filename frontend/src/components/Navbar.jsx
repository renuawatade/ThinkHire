import React from 'react'

export default function Navbar(){
  return (
    <div className="nav-modern">
      <div className="nav-left">
        <a href="/" className="brand-link">
          <span className="brand-icon">TH</span>
          <span className="brand-text">ThinkHire</span>
        </a>
      </div>

      <nav className="nav-center">
        <a href="#">Home</a>
        <a href="#about">About</a>
        <a href="#services">Services</a>
        <a href="#solutions">Solutions</a>
        <a href="#pages">Pages</a>
      </nav>

      <div className="nav-right">
        <a href="#contact" className="btn-primary">Contact Us</a>
      </div>
    </div>
  )
}
