'use client'
import { motion, AnimatePresence } from 'framer-motion'
import React from 'react'

interface ResetConfirmModalProps {
  isOpen: boolean
  onConfirm: () => void
  onCancel: () => void
}

export function ResetConfirmModal({ isOpen, onConfirm, onCancel }: ResetConfirmModalProps) {
  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            style={{
              position: 'fixed', inset: 0, zIndex: 100,
              background: 'rgba(0,0,0,0.75)',
              backdropFilter: 'blur(6px)',
            }}
          />

          {/* Modal */}
          <motion.div
            initial={{ opacity: 0, scale: 0.85, y: 40 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.85, y: 40 }}
            transition={{ type: 'spring', stiffness: 300, damping: 25 }}
            style={{
              position: 'fixed', inset: 0, zIndex: 101,
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              padding: '1rem',
            }}
          >
            <div style={{
              background: '#0F1229',
              border: `2px solid #FF5252`,
              borderRadius: '20px',
              padding: '2.5rem',
              maxWidth: '420px',
              width: '100%',
              boxShadow: `0 0 60px #FF525230, 0 0 120px #FF525210`,
              textAlign: 'center',
            }} className="z-50">
              {/* Emoji */}
              <motion.div
                animate={{ scale: [1, 1.2, 1] }}
                transition={{ duration: 0.6 }}
                style={{ fontSize: '3rem', marginBottom: '1rem' }}
              >
                ⚠️
              </motion.div>

              {/* Title */}
              <div style={{
                fontSize: '1.4rem', fontWeight: 800,
                color: '#FF5252',
                marginBottom: '0.5rem',
                letterSpacing: '0.05em',
              }}>
                RESET ALL PROGRESS?
              </div>

              {/* Message */}
              <div style={{
                background: '#FF525210',
                border: `1px solid #FF525230`,
                borderRadius: '10px',
                padding: '0.75rem 1rem',
                fontSize: '0.85rem',
                color: '#CBD5E1',
                marginBottom: '2rem',
                lineHeight: 1.5,
              }}>
                Are you sure? You will lose all the progress you made now. This action cannot be undone.
              </div>

              {/* Buttons */}
              <div style={{ display: 'flex', gap: '0.75rem' }}>
                <button
                  onClick={onCancel}
                  style={{
                    flex: 1, padding: '0.75rem',
                    borderRadius: '10px', border: '1px solid #1E2140',
                    background: '#131528', color: '#8892A4',
                    fontSize: '0.875rem', fontWeight: 600, cursor: 'pointer',
                  }}
                >
                  Stay Back
                </button>

                <button
                  onClick={onConfirm}
                  style={{
                    flex: 1, padding: '0.75rem',
                    borderRadius: '10px', border: 'none',
                    background: 'linear-gradient(135deg, #FF5252, #D32F2F)',
                    color: '#FFF',
                    fontSize: '0.875rem', fontWeight: 800, cursor: 'pointer',
                  }}
                >
                  Yes, Reset
                </button>
              </div>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  )
}
