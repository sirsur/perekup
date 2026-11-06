'use client'
import { useEffect } from 'react'

export default function ProgressBar() {
  useEffect(() => {
    const bar = document.getElementById('progress-bar')
    const nav = document.getElementById('nav')

    function onScroll() {
      if (bar) {
        const pct = (window.scrollY / (document.body.scrollHeight - window.innerHeight)) * 100
        bar.style.width = pct + '%'
      }
      if (nav) {
        nav.classList.toggle('scrolled', window.scrollY > 60)
      }
    }

    window.addEventListener('scroll', onScroll, { passive: true })
    return () => window.removeEventListener('scroll', onScroll)
  }, [])

  return <div id="progress-bar" />
}
