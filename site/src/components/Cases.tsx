import Image from 'next/image'

const CASES = [
    { src: '/cases/placeholder.svg', model: 'Range Rover Sport', note: 'Целый' },
    { src: '/cases/placeholder.svg', model: 'Mercedes-Benz G63', note: 'Целый' },
    { src: '/cases/placeholder.svg', model: 'Toyota Camry XSE', note: 'Целый' },
    { src: '/cases/placeholder.svg', model: 'Kia Rio', note: 'Ремонт' },
    { src: '/cases/placeholder.svg', model: 'Audi A5', note: 'Целый' },
    { src: '/cases/placeholder.svg', model: 'Mercedes-Benz C-class', note: 'Целый' },
    { src: '/cases/placeholder.svg', model: 'Lada Vesta', note: 'Ремонт' },
    { src: '/cases/placeholder.svg', model: 'Subaru Impreza', note: 'Ремонт' },
]

export default function Cases() {
    return (
        <section id='cases'>
            <div className='cases-head reveal'>
                <div>
                    <h2 className='s-title'>
                        Наши
                        <br />
                        <em>кейсы</em>
                    </h2>
                </div>
                <p className='process-desc'>
                    От премиального до автомобиля после ДТП – выкупаем в
                    любом состоянии по честной рыночной цене.
                </p>
            </div>

            <div className='cases-grid'>
                {CASES.map((c, i) => (
                    <div
                        className='case-card reveal'
                        key={c.src}
                        style={{ transitionDelay: (i % 4) * 0.08 + 's' }}
                    >
                        <span className='case-tag'>
                            {c.note.includes('Ремонт')
                                ? 'Любое состояние'
                                : 'Выкуплен'}
                        </span>
                        <Image
                            src={c.src}
                            alt={c.model}
                            fill
                            sizes='(max-width: 640px) 50vw, (max-width: 1100px) 33vw, 25vw'
                            style={{ objectFit: 'cover' }}
                        />
                        <div className='case-info'>
                            <div className='case-model'>{c.model}</div>
                        </div>
                    </div>
                ))}
            </div>
        </section>
    )
}
