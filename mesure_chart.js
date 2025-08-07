// mesure_chart.js - Affiche la courbe des mesures sur 24h en temps réel

let chart = null;
let data = {
    labels: [],
    datasets: [{
        label: 'Niveau (cm)',
        data: [],
        fill: false,
        borderColor: 'rgb(75, 192, 192)',
        tension: 0.1
    }]
};

function updateChart(newData) {
    data.labels = newData.labels;
    data.datasets[0].data = newData.values;
    if (chart) {
        chart.update();
    }
}

document.addEventListener('DOMContentLoaded', function() {
    const ctx = document.getElementById('mesureChart').getContext('2d');
    chart = new Chart(ctx, {
        type: 'line',
        data: data,
        options: {
            scales: {
                x: { type: 'time', time: { unit: 'hour', tooltipFormat: 'HH:mm' } },
                y: { beginAtZero: true }
            }
        }
    });

    // Rafraîchissement toutes les 5s
    setInterval(() => {
        fetch('/mesure_data')
            .then(resp => resp.json())
            .then(updateChart);
    }, 5000);
});
