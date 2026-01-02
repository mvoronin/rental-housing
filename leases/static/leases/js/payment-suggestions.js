/**
 * Payment Suggestions
 * Calculates and displays suggested payments based on last payment date
 */
(function() {
    const container = document.getElementById('payment-suggestions');
    const dataScript = document.getElementById('payment-suggestions-data');
    if (!container || !dataScript) return;

    const data = JSON.parse(dataScript.textContent);
    const { leaseStart, lastPeriod, currentRate, quickCreateUrl, csrfToken, labels } = data;

    if (!currentRate) {
        // No active rent rate, no suggestions
        return;
    }

    const today = new Date();
    today.setHours(0, 0, 0, 0);

    // Calculate suggested payments (reversed: newest first)
    const suggestions = calculateSuggestions(leaseStart, lastPeriod, currentRate, today).reverse();

    if (suggestions.length === 0) return;

    // Render suggestions
    render(container, suggestions, quickCreateUrl, csrfToken, labels);

    // Handle close buttons
    container.addEventListener('click', function(e) {
        if (e.target.classList.contains('suggestion-close')) {
            e.target.closest('.payment-suggestion').remove();
        }
    });

    function calculateSuggestions(leaseStart, lastPeriod, amount, today) {
        const suggestions = [];

        // Start from lease start or next month after last payment
        let nextPeriod;
        if (lastPeriod) {
            nextPeriod = new Date(lastPeriod);
            nextPeriod = addMonth(nextPeriod);
        } else {
            nextPeriod = new Date(leaseStart);
        }

        // Generate suggestions up to current month
        const currentMonth = new Date(today.getFullYear(), today.getMonth(), 1);

        while (nextPeriod <= currentMonth) {
            const overdueThreshold = addMonth(new Date(nextPeriod));
            const isOverdue = today >= overdueThreshold;

            suggestions.push({
                targetPeriod: nextPeriod.toISOString().split('T')[0],
                periodLabel: formatMonth(nextPeriod),
                amount: amount,
                status: isOverdue ? 'overdue' : 'planned'
            });

            nextPeriod = addMonth(nextPeriod);
        }

        return suggestions;
    }

    function addMonth(date) {
        const result = new Date(date);
        result.setMonth(result.getMonth() + 1);
        return result;
    }

    function formatMonth(date) {
        return date.toLocaleDateString(document.documentElement.lang || 'en', {
            year: 'numeric',
            month: 'long'
        });
    }

    function render(container, suggestions, url, csrfToken, labels) {
        const html = suggestions.map(s => {
            const statusLabel = s.status === 'overdue' ? labels.overdue : labels.planned;
            return `
            <div class="payment-suggestion suggestion-${s.status}">
                <button type="button" class="suggestion-close" title="Close">&times;</button>
                <div class="suggestion-info">
                    <strong>${s.amount}</strong> ${labels.for} <strong>${s.periodLabel}</strong>
                    <span class="badge badge-${s.status === 'overdue' ? 'danger' : 'info'}">${statusLabel}</span>
                </div>
                <button type="button" class="btn btn-primary"
                        data-status="${s.status}"
                        data-period="${s.targetPeriod}">
                    ${labels.add}
                </button>
            </div>
        `;
        }).join('');

        container.innerHTML = html;

        // Add click handlers
        container.querySelectorAll('button').forEach(btn => {
            btn.addEventListener('click', async function() {
                const status = this.dataset.status;
                const period = this.dataset.period;

                this.disabled = true;
                this.textContent = '...';

                try {
                    const formData = new FormData();
                    formData.append('status', status);
                    formData.append('target_period_start', period);

                    const response = await fetch(url, {
                        method: 'POST',
                        headers: {
                            'X-CSRFToken': csrfToken
                        },
                        body: formData
                    });

                    if (response.ok) {
                        // Reload to show new payment
                        window.location.reload();
                    } else {
                        const data = await response.json();
                        alert(data.error || 'Error creating payment');
                        this.disabled = false;
                        this.textContent = 'Add';
                    }
                } catch (err) {
                    alert('Error: ' + err.message);
                    this.disabled = false;
                    this.textContent = 'Add';
                }
            });
        });
    }
})();
