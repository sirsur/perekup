import ProgressBar from '@/components/ProgressBar'
import ScrollObserver from '@/components/ScrollObserver'
import Nav from '@/components/Nav'
import Hero from '@/components/Hero'
import Process from '@/components/Process'
import OfferForm from '@/components/OfferForm'
import Cases from '@/components/Cases'
import Cars from '@/components/Cars'
import Services from '@/components/Services'
import About from '@/components/About'
import Footer from '@/components/Footer'

export default function Home() {
  return (
    <>
      <ProgressBar />
      <ScrollObserver />
      <Nav />
      <Hero />
      <Process />
      <OfferForm />
      <Cases />
      <Cars />
      <Services />
      <About />
      <Footer />
    </>
  )
}
