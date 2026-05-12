const siteConfig = {
  companyName: "AFCyber SOLUTIONS",
  whatsappNumber: "18299198058",
  email: "info@afcybersolutions.com.do",
  location: "República Dominicana",
  defaultWhatsappMessage: "Hola AFCyber SOLUTIONS, quiero solicitar información sobre sus servicios tecnológicos.",
  socialLinks: {
    facebook: "#",
    instagram: "#",
    tiktok: "#",
    linkedin: "#"
  }
};

document.addEventListener("DOMContentLoaded", () => {
  document.body.classList.add("loaded");
  document.getElementById("currentYear").textContent = new Date().getFullYear();

  initAos();
  initNavbar();
  initWhatsappLinks();
  initContactForm();
  initCounters();
  initBackToTop();
  initNetworkCanvas();
});

function initAos() {
  if (window.AOS) {
    AOS.init({
      duration: 760,
      easing: "ease-out-cubic",
      once: true,
      offset: 80
    });
  }
}

function initNavbar() {
  const nav = document.getElementById("mainNav");
  const links = document.querySelectorAll(".premium-nav .nav-link");
  const menu = document.getElementById("navbarMenu");
  const collapse = menu ? bootstrap.Collapse.getOrCreateInstance(menu, { toggle: false }) : null;

  const updateNav = () => {
    nav.classList.toggle("nav-scrolled", window.scrollY > 30);
  };

  updateNav();
  window.addEventListener("scroll", updateNav, { passive: true });

  links.forEach((link) => {
    link.addEventListener("click", () => {
      links.forEach((item) => item.classList.remove("active"));
      link.classList.add("active");
      if (window.innerWidth < 992 && collapse) collapse.hide();
    });
  });
}

function buildWhatsappUrl(message) {
  return `https://wa.me/${siteConfig.whatsappNumber}?text=${encodeURIComponent(message || siteConfig.defaultWhatsappMessage)}`;
}

function initWhatsappLinks() {
  document.querySelectorAll(".js-whatsapp").forEach((link) => {
    const service = link.dataset.service;
    const message = link.dataset.message || (service
      ? `Hola AFCyber SOLUTIONS, quiero información sobre el servicio: ${service}.`
      : siteConfig.defaultWhatsappMessage);

    link.setAttribute("href", buildWhatsappUrl(message));
    link.setAttribute("target", "_blank");
    link.setAttribute("rel", "noopener");
  });
}

function initContactForm() {
  const form = document.getElementById("contactForm");
  if (!form) return;

  form.addEventListener("submit", (event) => {
    event.preventDefault();
    const data = new FormData(form);
    const name = String(data.get("name") || "").trim();
    const phone = String(data.get("phone") || "").trim();
    const email = String(data.get("email") || "").trim();
    const message = String(data.get("message") || "").trim();

    if (!name || !phone || !message) {
      showFormNotice(form, "Completa nombre, teléfono y mensaje.", "error");
      return;
    }

    const whatsappText = [
      "Hola AFCyber SOLUTIONS, quiero solicitar información.",
      "",
      `Nombre: ${name}`,
      `Teléfono: ${phone}`,
      email ? `Correo: ${email}` : "",
      `Mensaje: ${message}`
    ].filter(Boolean).join("\n");

    window.open(buildWhatsappUrl(whatsappText), "_blank", "noopener");
    showFormNotice(form, "Tu mensaje se preparó en WhatsApp.", "success");
    form.reset();
  });
}

function showFormNotice(form, text, type) {
  let notice = form.querySelector(".form-notice");
  if (!notice) {
    notice = document.createElement("div");
    notice.className = "form-notice";
    form.prepend(notice);
  }
  notice.textContent = text;
  notice.style.marginBottom = "1rem";
  notice.style.padding = ".85rem 1rem";
  notice.style.borderRadius = "8px";
  notice.style.fontWeight = "800";
  notice.style.color = "#fff";
  notice.style.background = type === "success" ? "rgba(16,185,129,.9)" : "rgba(239,68,68,.9)";
}

function initCounters() {
  const counters = document.querySelectorAll("[data-counter]");
  if (!counters.length) return;

  const observer = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (!entry.isIntersecting) return;
      animateCounter(entry.target);
      observer.unobserve(entry.target);
    });
  }, { threshold: 0.55 });

  counters.forEach((counter) => observer.observe(counter));
}

function animateCounter(element) {
  const target = Number(element.dataset.counter || "0");
  const duration = 1300;
  const start = performance.now();

  const tick = (now) => {
    const progress = Math.min((now - start) / duration, 1);
    const eased = 1 - Math.pow(1 - progress, 3);
    element.textContent = Math.round(target * eased);
    if (progress < 1) requestAnimationFrame(tick);
  };

  requestAnimationFrame(tick);
}

function initBackToTop() {
  const button = document.getElementById("backToTop");
  if (!button) return;

  window.addEventListener("scroll", () => {
    button.classList.toggle("show", window.scrollY > 600);
  }, { passive: true });

  button.addEventListener("click", () => {
    window.scrollTo({ top: 0, behavior: "smooth" });
  });
}

function initNetworkCanvas() {
  const canvas = document.getElementById("networkCanvas");
  if (!canvas) return;

  const ctx = canvas.getContext("2d");
  let points = [];
  let width = 0;
  let height = 0;
  let animationFrame = null;

  const resize = () => {
    const ratio = window.devicePixelRatio || 1;
    width = canvas.offsetWidth;
    height = canvas.offsetHeight;
    canvas.width = width * ratio;
    canvas.height = height * ratio;
    ctx.setTransform(ratio, 0, 0, ratio, 0, 0);
    points = createPoints(width, height);
  };

  const animate = () => {
    ctx.clearRect(0, 0, width, height);
    drawNetwork(ctx, points, width, height);
    points.forEach((point) => {
      point.x += point.vx;
      point.y += point.vy;
      if (point.x < 0 || point.x > width) point.vx *= -1;
      if (point.y < 0 || point.y > height) point.vy *= -1;
    });
    animationFrame = requestAnimationFrame(animate);
  };

  resize();
  animate();
  window.addEventListener("resize", () => {
    cancelAnimationFrame(animationFrame);
    resize();
    animate();
  });
}

function createPoints(width, height) {
  const amount = Math.min(78, Math.max(36, Math.floor(width / 18)));
  return Array.from({ length: amount }, () => ({
    x: Math.random() * width,
    y: Math.random() * height,
    vx: (Math.random() - 0.5) * 0.28,
    vy: (Math.random() - 0.5) * 0.28,
    r: Math.random() * 1.8 + 1
  }));
}

function drawNetwork(ctx, points) {
  ctx.lineWidth = 1;
  points.forEach((point, index) => {
    ctx.beginPath();
    ctx.arc(point.x, point.y, point.r, 0, Math.PI * 2);
    ctx.fillStyle = "rgba(46, 242, 255, .7)";
    ctx.fill();

    for (let i = index + 1; i < points.length; i += 1) {
      const other = points[i];
      const distance = Math.hypot(point.x - other.x, point.y - other.y);
      if (distance < 145) {
        const opacity = 1 - distance / 145;
        ctx.strokeStyle = `rgba(46, 242, 255, ${opacity * 0.16})`;
        ctx.beginPath();
        ctx.moveTo(point.x, point.y);
        ctx.lineTo(other.x, other.y);
        ctx.stroke();
      }
    }
  });
}
