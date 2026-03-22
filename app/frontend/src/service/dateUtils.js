
export function formatDate(value, { showTime = true, showSeconds = true, showYear = true } = {}) {
    if (!value) return '';
    const date = new Date(value);

    const day = String(date.getDate()).padStart(2, '0');
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const year = date.getFullYear();

    let formatted = `${day}.${month}`;
    if (showYear) {
        formatted += `.${year}`;
    }

    if (showTime) {
        const hours = String(date.getHours()).padStart(2, '0');
        const minutes = String(date.getMinutes()).padStart(2, '0');
        const seconds = String(date.getSeconds()).padStart(2, '0');
        formatted += ` ${hours}:${minutes}`;
        if (showSeconds) {
            formatted += `:${seconds}`;
        }
    }

    return formatted;
}
