import React from 'react';
import { Phone } from 'lucide-react';
import { Button } from './ui/button';

const EmergencyButton = ({ 
  className = '', 
  size = 'default',
  pulsing = false,
  onClick = null 
}) => {
  const handleEmergencyCall = () => {
    if (onClick) {
      onClick();
      return;
    }

    // Intentar llamar directamente al 112
    if ('navigator' in window && 'userAgent' in navigator) {
      const isMobile = /Android|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
      
      if (isMobile) {
        window.location.href = 'tel:112';
      } else {
        // En desktop, mostrar el número y copiarlo al portapapeles
        if (navigator.clipboard) {
          navigator.clipboard.writeText('112').then(() => {
            alert('Número 112 copiado al portapapeles. Usa tu teléfono para llamar.');
          }).catch(() => {
            alert('Llama al 112 desde tu teléfono para emergencias.');
          });
        } else {
          alert('Llama al 112 desde tu teléfono para emergencias.');
        }
      }
    }
  };

  const sizeClasses = {
    small: 'py-2 px-4 text-sm',
    default: 'py-4 px-6 text-base',
    large: 'py-6 px-8 text-lg',
    xl: 'py-8 px-12 text-xl'
  };

  return (
    <Button
      onClick={handleEmergencyCall}
      className={`
        emergency-button
        ${pulsing ? 'pulsing' : ''}
        ${sizeClasses[size]}
        ${className}
      `}
      aria-label="Llamar al 112 - Emergencias"
    >
      <Phone className="mr-2 h-5 w-5" />
      LLAMAR 112
    </Button>
  );
};

export default EmergencyButton;

