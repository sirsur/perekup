import { FiFileText, FiClock, FiMapPin, FiDollarSign } from 'react-icons/fi'

export default function Process() {
    return (
        <section id='process'>
            <div className='process-head reveal'>
                <div>
                    <h2 className='s-title'>
                        Как происходит
                        <br />
                        <em>процесс выкупа?</em>
                    </h2>
                </div>
                <p className='process-desc'>
                    Простая и прозрачная процедура. Заявки принимаем
                    круглосуточно, 7 дней в неделю – без скрытых комиссий.
                </p>
            </div>

            <div className='steps'>
                <div className='step reveal'>
                    <div className='step-num'>01</div>
                    <FiFileText className='step-ico' size={30} />
                    <div className='step-name'>Заявка 24/7</div>
                    <div className='step-text'>
                        Заполните форму или позвоните по номеру +7 (000)
                        000-00-00. Заявки принимаем круглосуточно.
                    </div>
                </div>

                <div
                    className='step reveal'
                    style={{ transitionDelay: '0.1s' }}
                >
                    <div className='step-num'>02</div>
                    <FiClock className='step-ico' size={30} />
                    <div className='step-name'>Оценка за 3 мин</div>
                    <div className='step-text'>
                        Честная оценка с учётом всего, что повышает стоимость
                        выкупа – состояние кузова, пробег, комплектация.
                    </div>
                </div>

                <div
                    className='step reveal'
                    style={{ transitionDelay: '0.2s' }}
                >
                    <div className='step-num'>03</div>
                    <FiMapPin className='step-ico' size={30} />
                    <div className='step-name'>Бесплатный выезд</div>
                    <div className='step-text'>
                        Бесплатно выезжаем к вам в любое удобное место в Сургуте
                        и ХМАО-ЯНАО. Осмотр без обязательств.
                    </div>
                </div>

                <div
                    className='step reveal'
                    style={{ transitionDelay: '0.3s' }}
                >
                    <div className='step-num'>04</div>
                    <FiDollarSign className='step-ico' size={30} />
                    <div className='step-name'>Оплата наличными</div>
                    <div className='step-text'>
                        Подписываем официальный договор купли-продажи. Расчёт
                        наличными в день обращения.
                    </div>
                </div>
            </div>
        </section>
    )
}
