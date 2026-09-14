clock = """
<div class="clock-container">
    <canvas id="clock"></canvas>
    <div id="time-text"></div>
</div>
<style>
    .clock-container {
        width: 100%;
        max-width: 110px;
        margin: 0 auto;
        text-align: center;
        font-family: Arial, sans-serif;
    }
    #clock {
        display: block;
        width: 100%;
        height: auto;
        aspect-ratio: 1 / 1;
    }
    #time-text {
        margin-top: 2px;
        color: rgba(255, 255, 255, 0.85);
        font-size: clamp(9px, 2.5vw, 11px);
        font-weight: 400;
        white-space: nowrap;
        letter-spacing: 0.2px;
    }
</style>
<script>
    const canvas = document.getElementById('clock');
    const ctx = canvas.getContext('2d');
    const timeText = document.getElementById('time-text');

    function resizeCanvas() {
        const size = canvas.getBoundingClientRect().width;
        const ratio = window.devicePixelRatio || 1;

        canvas.width = size * ratio;
        canvas.height = size * ratio;

        ctx.setTransform(ratio, 0, 0, ratio, 0, 0);
    }

    function hand(center, angle, length, width, tail = 0) {
        ctx.save();
        ctx.translate(center, center);
        ctx.rotate(angle);
        ctx.beginPath();
        ctx.moveTo(-tail, 0);
        ctx.lineTo(length, 0);
        ctx.strokeStyle = '#ffffff';
        ctx.lineWidth = width;
        ctx.lineCap = 'round';
        ctx.stroke();
        ctx.restore();
    }

    function drawClock() {
        const size = canvas.getBoundingClientRect().width;
        const center = size / 2;
        const radius = size * 0.46;

        const now = new Date();
        const ms = now.getMilliseconds();
        const seconds = now.getSeconds() + ms / 1000;
        const minutes = now.getMinutes() + seconds / 60;
        const hours = (now.getHours() % 12) + minutes / 60;

        ctx.clearRect(0, 0, size, size);

        ctx.beginPath();
        ctx.arc(center, center, radius, 0, Math.PI * 2);
        ctx.strokeStyle = 'rgba(255, 255, 255, 0.35)';
        ctx.lineWidth = Math.max(0.7, size * 0.01);
        ctx.stroke();

        for (let i = 0; i < 60; i++) {
            const angle = i * Math.PI / 30;
            const outer = radius - size * 0.02;
            const inner = i % 5 === 0
                ? radius - size * 0.07
                : radius - size * 0.04;

            ctx.beginPath();
            ctx.moveTo(
                center + Math.cos(angle) * inner,
                center + Math.sin(angle) * inner
            );
            ctx.lineTo(
                center + Math.cos(angle) * outer,
                center + Math.sin(angle) * outer
            );

            ctx.strokeStyle = i % 5 === 0
                ? 'rgba(255, 255, 255, 0.8)'
                : 'rgba(255, 255, 255, 0.25)';

            ctx.lineWidth = i % 5 === 0
                ? Math.max(1, size * 0.015)
                : Math.max(0.5, size * 0.007);

            ctx.stroke();
        }

        hand(
            center,
            hours * Math.PI / 6 - Math.PI / 2,
            radius * 0.52,
            Math.max(1.5, size * 0.03),
            size * 0.03
        );

        hand(
            center,
            minutes * Math.PI / 30 - Math.PI / 2,
            radius * 0.72,
            Math.max(1, size * 0.02),
            size * 0.04
        );

        hand(
            center,
            seconds * Math.PI / 30 - Math.PI / 2,
            radius * 0.83,
            Math.max(0.6, size * 0.01),
            size * 0.07
        );

        ctx.beginPath();
        ctx.arc(center, center, size * 0.025, 0, Math.PI * 2);
        ctx.fillStyle = '#ffffff';
        ctx.fill();

        const h = now.getHours();
        const m = now.getMinutes();

        timeText.textContent =
            `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}`;

        requestAnimationFrame(drawClock);
    }

    resizeCanvas();
    window.addEventListener('resize', resizeCanvas);
    drawClock();
</script>
"""