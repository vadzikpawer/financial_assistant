/**
 * Creates a doughnut chart
 * 
 * @param {CanvasRenderingContext2D} ctx - Canvas context
 * @param {Array} labels - Chart labels
 * @param {Array} data - Chart data
 */
function createDoughnutChart(ctx, labels, data) {
    return new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: labels,
            datasets: [{
                data: data,
                backgroundColor: [
                    '#3498db', '#2ecc71', '#9b59b6', '#e74c3c', '#f39c12',
                    '#1abc9c', '#d35400', '#c0392b', '#16a085', '#7f8c8d'
                ],
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'right',
                    labels: {
                        color: '#f8f9fa'
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            let label = context.label || '';
                            let value = context.raw || 0;
                            return label + ': ' + formatCurrency(value) + ' ₽';
                        }
                    }
                }
            }
        }
    });
}

/**
 * Creates a bar chart
 * 
 * @param {CanvasRenderingContext2D} ctx - Canvas context
 * @param {Array} labels - Chart labels
 * @param {Array} data - Chart data
 * @param {string} label - Dataset label
 */
function createBarChart(ctx, labels, data, label) {
    return new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: label,
                data: data,
                backgroundColor: '#3498db',
                borderColor: '#2980b9',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        color: '#f8f9fa',
                        callback: function(value) {
                            return formatCurrency(value) + ' ₽';
                        }
                    },
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    }
                },
                x: {
                    ticks: {
                        color: '#f8f9fa'
                    },
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    }
                }
            },
            plugins: {
                legend: {
                    labels: {
                        color: '#f8f9fa'
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            let label = context.dataset.label || '';
                            let value = context.raw || 0;
                            return label + ': ' + formatCurrency(value) + ' ₽';
                        }
                    }
                }
            }
        }
    });
}

/**
 * Creates a line chart
 * 
 * @param {CanvasRenderingContext2D} ctx - Canvas context
 * @param {Array} labels - Chart labels
 * @param {Array} data - Chart data
 * @param {string} label - Dataset label
 */
function createLineChart(ctx, labels, data, label) {
    return new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: label,
                data: data,
                backgroundColor: 'rgba(52, 152, 219, 0.2)',
                borderColor: '#3498db',
                borderWidth: 2,
                pointBackgroundColor: '#3498db',
                pointBorderColor: '#fff',
                pointRadius: 4,
                tension: 0.3
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        color: '#f8f9fa',
                        callback: function(value) {
                            return formatCurrency(value) + ' ₽';
                        }
                    },
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    }
                },
                x: {
                    ticks: {
                        color: '#f8f9fa'
                    },
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    }
                }
            },
            plugins: {
                legend: {
                    labels: {
                        color: '#f8f9fa'
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            let label = context.dataset.label || '';
                            let value = context.raw || 0;
                            return label + ': ' + formatCurrency(value) + ' ₽';
                        }
                    }
                }
            }
        }
    });
}

/**
 * Format a number as currency
 * 
 * @param {number} value - Number to format
 * @returns {string} Formatted number
 */
function formatCurrency(value) {
    return new Intl.NumberFormat('ru-RU').format(Math.round(value));
}
