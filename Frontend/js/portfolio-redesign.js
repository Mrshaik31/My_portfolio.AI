document.addEventListener("DOMContentLoaded", () => {
  // ==========================================
  // 1. Animated particle background
  // ==========================================
  const canvas = document.getElementById("universe");

  if (canvas) {
    const ctx = canvas.getContext("2d");
    let width = 0;
    let height = 0;
    let points = [];
    let frame = 0;

    const reduceMotion = window.matchMedia(
      "(prefers-reduced-motion: reduce)"
    ).matches;

    function resizeCanvas() {
      const dpr = Math.min(window.devicePixelRatio || 1, 1.8);

      width = window.innerWidth;
      height = window.innerHeight;

      canvas.width = Math.round(width * dpr);
      canvas.height = Math.round(height * dpr);
      canvas.style.width = `${width}px`;
      canvas.style.height = `${height}px`;

      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);

      const count = Math.min(
        115,
        Math.max(42, Math.floor((width * height) / 11500))
      );

      points = Array.from({ length: count }, () => ({
        x: Math.random() * width,
        y: Math.random() * height,
        vx: (Math.random() - 0.5) * 0.22,
        vy: (Math.random() - 0.5) * 0.22,
        radius: Math.random() * 1.5 + 0.35,
        purple: Math.random() > 0.72,
        alpha: Math.random() * 0.45 + 0.15
      }));
    }

    function drawBackground() {
      ctx.clearRect(0, 0, width, height);

      points.forEach((point, index) => {
        if (!reduceMotion) {
          point.x += point.vx;
          point.y += point.vy;
        }

        if (point.x < 0) point.x = width;
        if (point.x > width) point.x = 0;
        if (point.y < 0) point.y = height;
        if (point.y > height) point.y = 0;

        // Connect nearby particles.
        for (let j = index + 1; j < points.length; j++) {
          const other = points[j];
          const distance = Math.hypot(
            point.x - other.x,
            point.y - other.y
          );

          if (distance < 105) {
            const opacity = (1 - distance / 105) * 0.18;

            ctx.strokeStyle = point.purple
              ? `rgba(205, 85, 242, ${opacity})`
              : `rgba(27, 191, 231, ${opacity})`;

            ctx.lineWidth = 0.6;
            ctx.beginPath();
            ctx.moveTo(point.x, point.y);
            ctx.lineTo(other.x, other.y);
            ctx.stroke();
          }
        }

        ctx.beginPath();
        ctx.fillStyle = point.purple
          ? `rgba(230, 105, 245, ${point.alpha})`
          : `rgba(32, 216, 239, ${point.alpha})`;

        ctx.arc(point.x, point.y, point.radius, 0, Math.PI * 2);
        ctx.fill();
      });

      // Decorative network globe behind the hero.
      if (width > 620) {
        const centerX = width * (width < 850 ? 0.76 : 0.72);
        const centerY = height * 0.48;
        const radius = Math.min(width * 0.25, height * 0.37, 255);
        const rotation = reduceMotion ? 0 : frame * 0.0017;

        ctx.save();
        ctx.translate(centerX, centerY);

        for (let ring = 0; ring < 3; ring++) {
          ctx.save();
          ctx.rotate(rotation + ring * Math.PI / 3);

          ctx.strokeStyle =
            ring === 1
              ? "rgba(196, 77, 239, 0.35)"
              : "rgba(31, 195, 237, 0.30)";

          ctx.lineWidth = 1;
          ctx.beginPath();
          ctx.ellipse(
            0,
            0,
            radius,
            radius * (0.35 + ring * 0.13),
            ring * 0.4,
            0,
            Math.PI * 2
          );
          ctx.stroke();
          ctx.restore();
        }

        const nodes = [];

        for (let i = 0; i < 26; i++) {
          const angle = (i / 26) * Math.PI * 2 + rotation;
          const latitude = Math.sin(i * 2.31) * 0.9;

          nodes.push({
            x: Math.cos(angle) *
              Math.sqrt(1 - latitude * latitude) * radius,
            y: latitude * radius
          });
        }

        nodes.forEach((point, index) => {
          [1, 2].forEach((offset) => {
            const other = nodes[(index + offset) % nodes.length];

            ctx.strokeStyle =
              offset === 1
                ? "rgba(180, 75, 237, 0.48)"
                : "rgba(32, 183, 232, 0.25)";

            ctx.beginPath();
            ctx.moveTo(point.x, point.y);
            ctx.lineTo(other.x, other.y);
            ctx.stroke();
          });

          ctx.beginPath();
          ctx.fillStyle = index % 4 === 0 ? "#e878ef" : "#20d8ef";
          ctx.arc(point.x, point.y, 2.5, 0, Math.PI * 2);
          ctx.fill();
        });

        ctx.restore();
      }

      frame++;

      if (!reduceMotion) {
        requestAnimationFrame(drawBackground);
      }
    }

    resizeCanvas();
    drawBackground();

    window.addEventListener("resize", () => {
      resizeCanvas();

      if (reduceMotion) {
        drawBackground();
      }
    });
  }

  // ==========================================
  // 2. Reveal elements while scrolling
  // ==========================================
  const revealElements = document.querySelectorAll(".reveal");

  if (
    "IntersectionObserver" in window &&
    !window.matchMedia("(prefers-reduced-motion: reduce)").matches
  ) {
    const revealObserver = new IntersectionObserver(
      (entries, observer) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add("is-visible");
            observer.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.12 }
    );

    revealElements.forEach((element) => {
      revealObserver.observe(element);
    });
  } else {
    revealElements.forEach((element) => {
      element.classList.add("is-visible");
    });
  }

  // ==========================================
  // 3. Light/dark theme toggle
  // ==========================================
  const themeButton = document.getElementById("themeToggle");

  if (themeButton) {
    themeButton.addEventListener("click", () => {
      const root = document.documentElement;
      const switchToLight = root.dataset.theme !== "light";

      root.dataset.theme = switchToLight ? "light" : "dark";

      themeButton.innerHTML = switchToLight
        ? '<i class="bi bi-moon-stars"></i>'
        : '<i class="bi bi-sun"></i>';
    });
  }

  // ==========================================
  // 4. Connect portfolio buttons to chatbot
  // ==========================================
  document.querySelectorAll("[data-open-chat]").forEach((button) => {
    button.addEventListener("click", (event) => {
      event.preventDefault();

      const chatWindow = document.getElementById("chatbotWindow");
      const chatToggle = document.getElementById("chatbotToggle");

      if (!chatWindow || !chatToggle) {
        console.error("Chatbot HTML elements were not found.");
        return;
      }

      // Open the chatbot only if it is currently closed.
      if (!chatWindow.classList.contains("active")) {
        chatToggle.click();
      }
    });
  });

  // ==========================================
  // 5. Highlight the current navigation section
  // ==========================================
  const sections = document.querySelectorAll("main section[id]");
  const navLinks = document.querySelectorAll(
    '.top-nav a[href^="#"]'
  );

  if ("IntersectionObserver" in window) {
    const navObserver = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            navLinks.forEach((link) => {
              const isCurrent =
                link.getAttribute("href") === `#${entry.target.id}`;

              link.classList.toggle("current", isCurrent);
            });
          }
        });
      },
      {
        rootMargin: "-35% 0px -55% 0px"
      }
    );

    sections.forEach((section) => {
      navObserver.observe(section);
    });
  }
});