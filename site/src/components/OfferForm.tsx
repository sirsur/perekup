'use client'
import { useState } from 'react'
import Image from 'next/image'
import { FiTruck, FiTag, FiCalendar, FiClock, FiPhone } from 'react-icons/fi'

type Status = 'idle' | 'sending' | 'sent' | 'error'

export default function OfferForm() {
    const [status, setStatus] = useState<Status>('idle')
    const [form, setForm] = useState({
        brand: '',
        model: '',
        year: '',
        mileage: '',
        phone: '',
    })

    function update(field: keyof typeof form) {
        return (e: React.ChangeEvent<HTMLInputElement>) =>
            setForm((f) => ({ ...f, [field]: e.target.value }))
    }

    async function handleSubmit() {
        if (status === 'sending') return
        setStatus('sending')
        try {
            const res = await fetch('/api/lead', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(form),
            })
            if (!res.ok) throw new Error('request failed')
            setStatus('sent')
            setForm({ brand: '', model: '', year: '', mileage: '', phone: '' })
            setTimeout(() => setStatus('idle'), 4000)
        } catch {
            setStatus('error')
            setTimeout(() => setStatus('idle'), 4000)
        }
    }

    const buttonLabel =
        status === 'sending'
            ? 'Отправляем…'
            : status === 'sent'
            ? '✓ Заявка принята'
            : status === 'error'
            ? 'Ошибка, повторите'
            : 'Узнать стоимость'

    return (
        <section id='offer'>
            <div className='rbf-card reveal'>
                {/* Left: form */}
                <div className='rbf-left'>
                    <h2 className='rbf-heading'>Продайте авто</h2>

                    {/* Марка / Модель */}
                    <div className='rbf-input-group'>
                        <div className='rbf-field-row'>
                            <div className='rbf-field-icon'>
                                <FiTruck size={16} />
                            </div>
                            <input
                                type='text'
                                className='rbf-field-input'
                                placeholder='Марка авто'
                                value={form.brand}
                                onChange={update('brand')}
                            />
                        </div>
                        <hr className='rbf-divider' />
                        <div className='rbf-field-row'>
                            <div className='rbf-field-icon'>
                                <FiTag size={16} />
                            </div>
                            <input
                                type='text'
                                className='rbf-field-input'
                                placeholder='Модель'
                                value={form.model}
                                onChange={update('model')}
                            />
                        </div>
                    </div>

                    {/* Год / Пробег */}
                    <div className='rbf-dt-row'>
                        <div className='rbf-dt-cell'>
                            <FiCalendar size={15} />
                            <input
                                type='number'
                                placeholder='Год выпуска'
                                min='1990'
                                max='2025'
                                value={form.year}
                                onChange={update('year')}
                            />
                        </div>
                        <div className='rbf-dt-cell'>
                            <FiClock size={15} />
                            <input
                                type='number'
                                placeholder='Пробег, км'
                                value={form.mileage}
                                onChange={update('mileage')}
                            />
                        </div>
                    </div>

                    {/* Phone */}
                    <div className='rbf-phone-row'>
                        <FiPhone size={15} />
                        <input
                            type='tel'
                            className='rbf-phone-input'
                            placeholder='+7 (000) 000-00-00'
                            value={form.phone}
                            onChange={update('phone')}
                        />
                    </div>

                    {/* Actions */}
                    <div className='rbf-actions'>
                        <button
                            type='button'
                            className='rbf-submit'
                            onClick={handleSubmit}
                            disabled={status === 'sending'}
                            style={
                                status === 'sent'
                                    ? { background: '#fff', color: '#000' }
                                    : undefined
                            }
                        >
                            {buttonLabel}
                        </button>
                    </div>
                </div>

                {/* Right: image */}
                <div className='rbf-right'>
                    <Image
                        src='/cases/placeholder.svg'
                        alt='Выкуп автомобилей в Сургуте'
                        fill
                        style={{ objectFit: 'cover' }}
                    />
                </div>
            </div>
        </section>
    )
}
