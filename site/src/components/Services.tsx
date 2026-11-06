import { FiZap, FiCreditCard, FiEdit3, FiMapPin } from 'react-icons/fi'

const SERVICES = [
    {
        num: '01',
        title: 'Срочный выкуп',
        desc: 'Выкупаем автомобиль в течение 24 часов в любом состоянии. Звоните – приедем и рассчитаемся сразу.',
        icon: <FiZap size={22} />,
    },
    {
        num: '02',
        title: 'Выкуп из залога',
        desc: 'Выкупаем кредитные и залоговые авто. Помогаем снять ограничения ГИБДД и закрыть долг перед банком.',
        icon: <FiCreditCard size={22} />,
    },
    {
        num: '03',
        title: 'Оформление сделки',
        desc: 'Полное юридическое сопровождение: договор, снятие с учёта, перевод средств.',
        icon: <FiEdit3 size={22} />,
    },
    {
        num: '04',
        title: 'Бесплатный выезд',
        desc: 'Специалист бесплатно выезжает к вам – в любое место Сургута, ХМАО и ЯНАО в удобное вам время.',
        icon: <FiMapPin size={22} />,
    },
]

export default function Services() {
    return (
        <section id='services'>
            <div className='reveal'>
                <h2 className='s-title'>
                    Наши
                    <br />
                    <em>услуги</em>
                </h2>
            </div>
            <div className='services-grid'>
                {SERVICES.map((s, i) => (
                    <div
                        className='sc reveal'
                        key={s.num}
                        style={{ transitionDelay: i * 0.1 + 's' }}
                    >
                        <div className='sc-num'>{s.num}</div>
                        <div className='sc-icon'>{s.icon}</div>
                        <div className='sc-title'>{s.title}</div>
                        <div className='sc-desc'>{s.desc}</div>
                    </div>
                ))}
            </div>
        </section>
    )
}
