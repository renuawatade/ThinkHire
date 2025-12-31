import React from 'react'
import Navbar from './components/Navbar'
import Hero from './components/Hero'
import Steps from './components/Steps'
import UploadDropzone from './components/UploadDropzone'
import ExtractedDetails from './components/ExtractedDetails'
import Footer from './components/Footer'

// Root App: Arranges top-level sections of the landing page
export default function App() {
  return (
    <div className="min-h-screen bg-white">
      <header className="header-shadow">
        <div className="container mx-auto px-4">
          <Navbar />
        </div>
      </header>

      <main className="container mx-auto px-4">
        <Hero />

        <section className="mt-12">
          {/* lightweight features preview - keep content minimal for landing */}
          <div className="features-grid">
            <div className="feature card-shadow">Smart Resume Parsing</div>
            <div className="feature card-shadow">AI Job Matching</div>
            <div className="feature card-shadow">Instant Shortlisting</div>
            <div className="feature card-shadow">Secure & Compliant</div>
          </div>
        </section>
      </main>

      <Footer />
    </div>
  )
}
