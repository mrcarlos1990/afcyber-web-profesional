const siteConfig = {
  whatsappNumber: window.AF_SITE?.whatsapp || "18299198058",
  defaultWhatsappMessage: window.AF_SITE?.defaultMessage || "Hola AFCyber Solutions, quiero solicitar informacion sobre sus servicios."
};

const serviceMessages = {
  "Sistema POS": "Hola AFCyber Solutions, me interesa una cotizacion para un Sistema POS.",
  "Sistemas POS / ERP": "Hola AFCyber Solutions, me interesa una cotizacion para un Sistema POS.",
  "Landing Page": "Hola AFCyber Solutions, necesito una Landing Page profesional.",
  "Landing Pages y Webs": "Hola AFCyber Solutions, necesito una Landing Page profesional.",
  "CCTV": "Hola AFCyber Solutions, deseo una cotizacion para camaras de seguridad.",
  "CCTV y Control de Acceso": "Hola AFCyber Solutions, deseo una cotizacion para camaras de seguridad.",
  "Desarrollo Web": "Hola AFCyber Solutions, necesito una pagina web profesional.",
  "Software Empresarial": "Hola AFCyber Solutions, necesito desarrollo de software empresarial.",
  "Aire Acondicionado": "Hola AFCyber Solutions, necesito servicio para aire acondicionado.",
  "Aires Acondicionados": "Hola AFCyber Solutions, necesito servicio para aire acondicionado.",
  "Soporte Tecnico": "Hola AFCyber Solutions, necesito soporte tecnico.",
  "Mantenimiento de Computadoras": "Hola AFCyber Solutions, necesito mantenimiento de computadoras.",
  "Instalacion de Software": "Hola AFCyber Solutions, necesito instalacion de software.",
  "Ciberseguridad": "Hola AFCyber Solutions, quiero una cotizacion para ciberseguridad basica."
};

document.addEventListener("DOMContentLoaded", () => {
  document.body.classList.add("loaded");

  const year = document.getElementById("currentYear");
  if (year) year.textContent = new Date().getFullYear();

  initAos();
  initNavbar();
  initWhatsappLinks();
  initContactForm();
  initCounters();
  initBackToTop();
  initNetworkCanvas();
  initInteractiveTimeline();
  initHelpBot();
  initServiceFilters();
  initSmartServiceSelect();
  initSmoothScroll();
});

function initAos() {
  if (!window.AOS) return;
  AOS.init({ duration: 760, easing: "ease-out-cubic", once: true, offset: 70 });
}

function getLinkHash(link) {
  const href = link.getAttribute("href") || "";
  if (!href.includes("#")) return "";
  return `#${href.split("#").pop()}`;
}

function initNavbar() {
  const nav = document.getElementById("mainNav");
  const menu = document.getElementById("navbarMenu");
  const links = document.querySelectorAll(".nav-link, .navbar-brand");
  const collapse = menu && window.bootstrap
    ? bootstrap.Collapse.getOrCreateInstance(menu, { toggle: false })
    : null;

  if (!nav) return;

  const updateNav = () => nav.classList.toggle("nav-scrolled", window.scrollY > 30);
  updateNav();
  window.addEventListener("scroll", updateNav, { passive: true });

  links.forEach((link) => {
    link.addEventListener("click", () => {
      if (window.innerWidth < 1200 && collapse && menu.classList.contains("show")) {
        setTimeout(() => collapse.hide(), 120);
      }
    });
  });

  const targets = Array.from(links)
    .map((link) => getLinkHash(link))
    .filter(Boolean)
    .map((hash) => document.querySelector(hash))
    .filter(Boolean);

  if (!targets.length || !("IntersectionObserver" in window)) return;

  const observer = new IntersectionObserver((entries) => {
    const visible = entries
      .filter((entry) => entry.isIntersecting)
      .sort((a, b) => b.intersectionRatio - a.intersectionRatio)[0];
    if (!visible) return;
    links.forEach((link) => link.classList.toggle("active", getLinkHash(link) === `#${visible.target.id}`));
  }, { threshold: [0.18, 0.42, 0.66], rootMargin: "-18% 0px -56% 0px" });

  targets.forEach((target) => observer.observe(target));
}

function initSmoothScroll() {
  document.querySelectorAll('a[href*="#"]').forEach((anchor) => {
    anchor.addEventListener("click", function handleAnchorClick(event) {
      const targetId = getLinkHash(this);
      if (!targetId || targetId === "#") return;
      const targetElement = document.querySelector(targetId);
      if (!targetElement) return;
      event.preventDefault();
      targetElement.scrollIntoView({ behavior: "smooth", block: "start" });
      history.replaceState(null, "", targetId);
    });
  });
}

function buildWhatsappUrl(message) {
  const normalizedMessage = String(message || siteConfig.defaultWhatsappMessage).trim();
  const number = String(siteConfig.whatsappNumber || "").replace(/\D/g, "") || "18299198058";
  return `https://wa.me/${number}?text=${encodeURIComponent(normalizedMessage)}`;
}

function initWhatsappLinks() {
  document.querySelectorAll(".js-whatsapp").forEach((link) => {
    const service = link.dataset.service;
    const message = link.dataset.message || serviceMessages[service] || (service
      ? `Hola AFCyber Solutions, quiero informacion sobre: ${service}.`
      : siteConfig.defaultWhatsappMessage);

    link.setAttribute("href", buildWhatsappUrl(message));
    link.setAttribute("target", "_blank");
    link.setAttribute("rel", "noopener");
  });
}

function initSmartServiceSelect() {
  const select = document.querySelector('[name="requested_service"]');
  const form = document.querySelector("#contacto .contact-form");
  if (!select || !form) return;

  select.addEventListener("change", () => {
    const message = serviceMessages[select.value];
    form.dataset.whatsappMessage = message || siteConfig.defaultWhatsappMessage;
  });
}

function initContactForm() {
  const form = document.querySelector("#contacto .contact-form");
  if (!form) return;

  const status = form.querySelector(".form-status");

  form.querySelectorAll(".form-control").forEach((field) => {
    field.addEventListener("blur", () => {
      field.classList.toggle("is-valid", field.checkValidity() && field.value.trim() !== "");
      field.classList.toggle("is-invalid", !field.checkValidity() && field.required);
    });
  });

  form.addEventListener("submit", (event) => {
    form.classList.add("was-validated");

    if (!form.checkValidity()) {
      event.preventDefault();
      if (status) {
        status.textContent = "Revisa los campos marcados antes de enviar.";
        status.className = "form-status show error";
      }
      form.reportValidity();
      return;
    }

    if (status) {
      status.textContent = "Solicitud lista. Enviando tus datos de forma segura...";
      status.className = "form-status show success";
    }
  });
}

function initInteractiveTimeline() {
  const items = document.querySelectorAll(".process-step");
  if (!items.length) return;
  items.forEach((item) => {
    item.addEventListener("mouseenter", () => {
      items.forEach((entry) => entry.classList.remove("active"));
      item.classList.add("active");
    });
    item.addEventListener("focusin", () => {
      items.forEach((entry) => entry.classList.remove("active"));
      item.classList.add("active");
    });
  });
}

function initHelpBot() {
  const bot = document.getElementById("helpBot");
  if (!bot) return;

  const toggle = bot.querySelector(".help-bot-toggle");
  const close = bot.querySelector(".help-bot-close");
  const setOpen = (isOpen) => {
    bot.classList.toggle("open", isOpen);
    if (toggle) toggle.setAttribute("aria-expanded", String(isOpen));
  };

  if (toggle) toggle.addEventListener("click", () => setOpen(!bot.classList.contains("open")));
  if (close) close.addEventListener("click", () => setOpen(false));
}

function initServiceFilters() {
  const buttons = document.querySelectorAll(".filter-btn");
  const items = document.querySelectorAll(".gallery-item");
  if (!buttons.length || !items.length) return;

  buttons.forEach((button) => {
    button.addEventListener("click", () => {
      const filter = button.dataset.filter || "all";
      buttons.forEach((entry) => entry.classList.toggle("active", entry === button));
      items.forEach((item) => {
        const visible = filter === "all" || item.dataset.category === filter;
        item.classList.toggle("is-hidden", !visible);
      });
    });
  });
}

function initCounters() {
  const counters = document.querySelectorAll("[data-counter]");
  if (!counters.length) return;

  const startCounter = (counter) => {
    if (counter.dataset.counterAnimated === "true") return;
    counter.dataset.counterAnimated = "true";
    animateCounter(counter);
  };

  if (!("IntersectionObserver" in window)) {
    counters.forEach(startCounter);
    return;
  }

  const observer = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (!entry.isIntersecting) return;
      startCounter(entry.target);
      observer.unobserve(entry.target);
    });
  }, { threshold: 0.55 });

  counters.forEach((counter) => {
    counter.textContent = "0";
    observer.observe(counter);
  });
}

function animateCounter(element) {
  const target = Number(element.dataset.counter || "0");
  const duration = 1800;
  const start = performance.now();

  const tick = (now) => {
    const progress = Math.min((now - start) / duration, 1);
    const easedProgress = 1 - Math.pow(1 - progress, 3);
    element.textContent = String(Math.round(target * easedProgress));
    if (progress < 1) {
      requestAnimationFrame(tick);
      return;
    }
    element.textContent = String(target);
  };

  requestAnimationFrame(tick);
}

function initBackToTop() {
  const button = document.getElementById("backToTop");
  if (!button) return;
  window.addEventListener("scroll", () => button.classList.toggle("show", window.scrollY > 650), { passive: true });
  button.addEventListener("click", () => window.scrollTo({ top: 0, behavior: "smooth" }));
}

function initNetworkCanvas() {
  const hero = document.getElementById("inicio");
  const canvas = document.getElementById("networkCanvas");
  if (!hero || !canvas) return;

  const ctx = canvas.getContext("2d");
  const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  let points = [];
  let width = 0;
  let height = 0;
  let animationFrame = null;
  let isHeroVisible = true;

  const resize = () => {
    const ratio = Math.min(window.devicePixelRatio || 1, 2);
    width = canvas.offsetWidth;
    height = canvas.offsetHeight;
    canvas.width = width * ratio;
    canvas.height = height * ratio;
    ctx.setTransform(ratio, 0, 0, ratio, 0, 0);
    points = createPoints(width, height);
  };

  const stopAnimation = () => {
    if (!animationFrame) return;
    cancelAnimationFrame(animationFrame);
    animationFrame = null;
  };

  const animate = () => {
    ctx.clearRect(0, 0, width, height);
    drawNetwork(ctx, points);
    movePoints(points, width, height);
    animationFrame = requestAnimationFrame(animate);
  };

  const startAnimation = () => {
    if (animationFrame || reduceMotion) return;
    animationFrame = requestAnimationFrame(animate);
  };

  resize();
  drawNetwork(ctx, points);
  startAnimation();

  if ("IntersectionObserver" in window) {
    const observer = new IntersectionObserver((entries) => {
      isHeroVisible = entries.some((entry) => entry.isIntersecting);
      if (isHeroVisible) startAnimation();
      else stopAnimation();
    }, { threshold: 0.08 });
    observer.observe(hero);
  }

  window.addEventListener("resize", () => {
    stopAnimation();
    resize();
    drawNetwork(ctx, points);
    if (isHeroVisible) startAnimation();
  }, { passive: true });
}

function createPoints(width, height) {
  const baseAmount = Math.min(82, Math.max(34, Math.floor(width / 18)));
  const amount = width < 768 ? Math.round(baseAmount / 2) : baseAmount;
  return Array.from({ length: amount }, () => ({
    x: Math.random() * width,
    y: Math.random() * height,
    vx: (Math.random() - .5) * .22,
    vy: (Math.random() - .5) * .22,
    r: Math.random() * 1.6 + .8
  }));
}

function movePoints(points, width, height) {
  points.forEach((point) => {
    point.x += point.vx;
    point.y += point.vy;
    if (point.x < 0 || point.x > width) point.vx *= -1;
    if (point.y < 0 || point.y > height) point.vy *= -1;
  });
}

function drawNetwork(ctx, points) {
  ctx.lineWidth = 1;
  points.forEach((point, index) => {
    ctx.beginPath();
    ctx.arc(point.x, point.y, point.r, 0, Math.PI * 2);
    ctx.fillStyle = "rgba(34, 211, 238, .76)";
    ctx.shadowColor = "rgba(34, 211, 238, .72)";
    ctx.shadowBlur = 8;
    ctx.fill();
    ctx.shadowBlur = 0;

    for (let i = index + 1; i < points.length; i += 1) {
      const other = points[i];
      const distance = Math.hypot(point.x - other.x, point.y - other.y);
      if (distance < 132) {
        const opacity = 1 - distance / 132;
        ctx.strokeStyle = `rgba(34, 211, 238, ${opacity * .18})`;
        ctx.beginPath();
        ctx.moveTo(point.x, point.y);
        ctx.lineTo(other.x, other.y);
        ctx.stroke();
      }
    }
  });
}
