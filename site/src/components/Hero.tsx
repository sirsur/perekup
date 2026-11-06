import Image from 'next/image'

export default function Hero() {
    return (
        <section id='hero'>
            <div className='hero-bg'>
                <Image
                    src='/hero-car.jpg'
                    alt='Выкуп автомобилей в любом состоянии'
                    fill
                    priority
                    style={{ objectFit: 'cover' }}
                    sizes='100vw'
                />
                <div className='hero-bg-overlay' />
            </div>

            <div className='hero-content'>
                <h1 className='hero-title'>
                    <span className='tl'>
                        <span className='ti'>Продай свое</span>
                    </span>
                    <span className='tl'>
                        <span className='ti ac'>авто</span>
                    </span>
                </h1>
                <p className='hero-sub'>
                    Выкуп в любом состоянии – до 90% рыночной стоимости.
                    Выгодная продажа за 30 минут, деньги в день обращения.
                </p>
                <div className='hero-btns'>
                    <a href='#offer' className='btn-p'>
                        Получить оценку
                    </a>
                    <a href='#process' className='btn-s'>
                        Как это работает
                    </a>
                </div>
            </div>
        </section>
    )
}
