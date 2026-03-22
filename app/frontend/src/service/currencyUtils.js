export function currencySymbol(code) {
  const map = {
    UAH: '₴',
    USD: '$',
    EUR: '€',
    PLN: 'zł',
    RUB: '₽'
  };
  return map[code] || code;
}

export function formatPrice(value, currencyCode) {
  if (typeof value !== 'number') return '';
  const symbol = currencySymbol(currencyCode);
  return `${value.toLocaleString('ru-RU', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} ${symbol}`;
}
