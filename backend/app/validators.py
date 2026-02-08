"""
DigIdentity Engine — Validators
Funzioni di validazione per email, telefono e altri input.
"""

import re
from typing import Optional


def validate_email(email: str) -> bool:
    """
    Valida formato email.
    
    Args:
        email: Indirizzo email da validare
        
    Returns:
        bool: True se valido, False altrimenti
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_italian_phone(phone: str) -> bool:
    """
    Valida formato telefono italiano.
    Accetta formati: +39 xxx xxx xxxx, 3xx xxx xxxx, +393xxxxxxxxx
    
    Args:
        phone: Numero di telefono da validare
        
    Returns:
        bool: True se valido, False altrimenti
    """
    # Rimuovi spazi, trattini, parentesi
    cleaned = re.sub(r'[\s\-\(\)]', '', phone)
    
    # Pattern per numeri italiani
    patterns = [
        r'^\+39\d{9,10}$',  # +39xxxxxxxxx
        r'^00\d{9,10}$',     # 00xxxxxxxxx
        r'^3\d{8,9}$',       # 3xxxxxxxx (mobile)
        r'^0\d{9,10}$',      # 0xxxxxxxxx (fisso)
    ]
    
    return any(re.match(pattern, cleaned) for pattern in patterns)


def normalize_phone(phone: str) -> str:
    """
    Normalizza numero di telefono italiano in formato internazionale.
    
    Args:
        phone: Numero di telefono da normalizzare
        
    Returns:
        str: Numero normalizzato in formato +39xxxxxxxxxx
    """
    # Rimuovi spazi, trattini, parentesi
    cleaned = re.sub(r'[\s\-\(\)]', '', phone)
    
    # Se inizia con +39, lascialo così
    if cleaned.startswith('+39'):
        return cleaned
    
    # Se inizia con 00, sostituisci con +
    if cleaned.startswith('00'):
        return '+' + cleaned[2:]
    
    # Se inizia con 3 o 0 (numero italiano senza prefisso), aggiungi +39
    if cleaned.startswith(('3', '0')):
        return '+39' + cleaned
    
    # Altrimenti restituisci così com'è
    return cleaned


def validate_url(url: Optional[str]) -> bool:
    """
    Valida formato URL.
    
    Args:
        url: URL da validare (può essere None)
        
    Returns:
        bool: True se valido o None, False altrimenti
    """
    if url is None or url.strip() == '':
        return True  # URL opzionale
    
    pattern = r'^https?://[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(/.*)?$'
    return bool(re.match(pattern, url))


def sanitize_input(text: str, max_length: int = 500) -> str:
    """
    Sanitizza input testuale per prevenire XSS e injection.
    
    Args:
        text: Testo da sanitizzare
        max_length: Lunghezza massima consentita
        
    Returns:
        str: Testo sanitizzato
    """
    # Rimuovi caratteri pericolosi
    sanitized = re.sub(r'[<>\"\'%;()&+]', '', text)
    
    # Limita lunghezza
    sanitized = sanitized[:max_length]
    
    # Rimuovi spazi multipli
    sanitized = re.sub(r'\s+', ' ', sanitized).strip()
    
    return sanitized
