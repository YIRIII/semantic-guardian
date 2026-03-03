Chart.defaults.font.family = "'Tajawal', sans-serif";

async function loadTrustHistogram(canvasId, url) {
    const resp = await fetch(url);
    const data = await resp.json();

    new Chart(document.getElementById(canvasId), {
        type: 'bar',
        data: {
            labels: data.labels,
            datasets: [{
                label: 'عدد السجلات',
                data: data.data,
                backgroundColor: data.data.map((_, i) => {
                    const ratio = i / (data.labels.length - 1);
                    if (ratio < 0.4) return 'rgba(220, 38, 38, 0.7)';
                    if (ratio < 0.7) return 'rgba(234, 88, 12, 0.7)';
                    return 'rgba(22, 163, 74, 0.7)';
                }),
                borderRadius: 4,
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: { display: false },
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: { stepSize: 1 },
                    title: { display: true, text: 'العدد' }
                },
                x: {
                    title: { display: true, text: 'درجة الثقة' }
                }
            }
        }
    });
}

async function loadDoughnutChart(canvasId, url) {
    const resp = await fetch(url);
    const data = await resp.json();

    new Chart(document.getElementById(canvasId), {
        type: 'doughnut',
        data: {
            labels: data.labels,
            datasets: [{
                data: data.data,
                backgroundColor: [
                    'rgba(22, 163, 74, 0.8)',
                    'rgba(220, 38, 38, 0.8)',
                ],
                borderWidth: 2,
                borderColor: '#fff',
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: { padding: 20, font: { size: 14 } }
                }
            }
        }
    });
}
