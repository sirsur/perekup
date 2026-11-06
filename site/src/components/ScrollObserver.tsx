'use client'
import { useEffect } from 'react'

export default function ScrollObserver() {
  useEffect(() => {
    const obs = new IntersectionObserver(
      (entries) => {
        entries.forEach((e) => {
          if (e.isIntersecting) e.target.classList.add('in')
        })
      },
      { threshold: 0.08 },
    )
    document.querySelectorAll('.reveal').forEach((el) => obs.observe(el))
    return () => obs.disconnect()
  }, [])

  return null
}
