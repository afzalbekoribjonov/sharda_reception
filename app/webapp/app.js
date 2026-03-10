(function () {
  const tg = window.Telegram?.WebApp;

  const el = (id) => document.getElementById(id);

  const form = el("form");
  const fullName = el("fullName");
  const phone = el("phone");
  const errName = el("errName");
  const errPhone = el("errPhone");
  const submitBtn = el("submitBtn");
  const spinner = el("spinner");
  const toast = el("toast");
  const closeBtn = el("closeBtn");
  const langBtn = el("langBtn");

  const I18N = {
    uz: {
      title: "Ro'yxatdan o'tish",
      subtitle: "Ma'lumotlarni kiriting",
      hint: "Bu ma'lumotlar ro'yxatdan o'tishni davom ettirish uchun kerak bo'ladi.",
      name_label: 'Ism familiya',
      phone_label: 'Telefon raqam',
      phone_help: 'Raqamni 9 xonada kiriting (masalan 901234567)',
      submit: 'Yuborish',
      close: 'Yopish',
      footer: "Ma'lumotlar faqat ro'yxatdan o'tish uchun ishlatiladi.",
      err_name_required: 'Ism familiya kiriting.',
      err_name_short: 'Ism familiya juda qisqa.',
      err_phone_required: 'Telefon raqam kiriting.',
      err_phone_invalid: "Telefon raqam noto'g'ri. 9 ta raqam kiriting.",
      sending: 'Yuborilmoqda...',
      sent: 'Yuborildi ✅',
    },
    ru: {
      title: 'Регистрация',
      subtitle: 'Введите данные',
      hint: 'Эти данные нужны, чтобы продолжить регистрацию.',
      name_label: 'Имя и фамилия',
      phone_label: 'Телефон',
      phone_help: 'Введите 9 цифр (например 901234567)',
      submit: 'Отправить',
      close: 'Закрыть',
      footer: 'Данные используются только для регистрации.',
      err_name_required: 'Введите имя и фамилию.',
      err_name_short: 'Слишком коротко.',
      err_phone_required: 'Введите номер телефона.',
      err_phone_invalid: 'Неверный номер. Введите 9 цифр.',
      sending: 'Отправка...',
      sent: 'Отправлено ✅',
    },
    en: {
      title: 'Registration',
      subtitle: 'Enter your details',
      hint: 'These details are required to continue registration.',
      name_label: 'Full name',
      phone_label: 'Phone number',
      phone_help: 'Enter 9 digits (e.g. 901234567)',
      submit: 'Submit',
      close: 'Close',
      footer: 'Data is used only for registration.',
      err_name_required: 'Enter your full name.',
      err_name_short: 'Name is too short.',
      err_phone_required: 'Enter your phone number.',
      err_phone_invalid: 'Invalid phone. Enter 9 digits.',
      sending: 'Sending...',
      sent: 'Sent ✅',
    },
  };

  function guessLang() {
    // priority: query param ?lang=uz | tg user language_code | default uz
    const qp = new URLSearchParams(location.search);
    const qLang = (qp.get("lang") || "").toLowerCase();
    if (I18N[qLang]) return qLang;

    const lc = tg?.initDataUnsafe?.user?.language_code;
    if (!lc) return "uz";
    const l = lc.toLowerCase();
    if (l.startsWith("ru")) return "ru";
    if (l.startsWith("en")) return "en";
    if (l.startsWith("uz")) return "uz";
    return "uz";
  }

  let lang = guessLang();

  function applyTheme() {
    if (!tg) return;
    tg.ready();
    tg.expand();

    const p = tg.themeParams || {};
    // map telegram theme colors if available
    const bg = p.bg_color || null;
    const text = p.text_color || null;
    const hint = p.hint_color || null;
    const button = p.button_color || null;
    const buttonText = p.button_text_color || null;

    const root = document.documentElement;

    if (bg) root.style.setProperty("--bg", bg);
    if (text) root.style.setProperty("--text", text);
    if (hint) root.style.setProperty("--muted", hint);

    // Use Telegram button color as primary if present
    if (button) root.style.setProperty("--primary", button);
    if (buttonText) {
      submitBtn.style.color = buttonText;
      spinner.style.borderColor = `rgba(255,255,255,.25)`;
      spinner.style.borderTopColor = buttonText;
    }
  }

  function t() {
    return I18N[lang] || I18N.uz;
  }

  function setText() {
    const tr = t();
    document.documentElement.lang = lang;

    el("t_title").textContent = tr.title;
    el("t_subtitle").textContent = tr.subtitle;
    el("t_hint").textContent = tr.hint;
    el("t_name_label").textContent = tr.name_label;
    el("t_phone_label").textContent = tr.phone_label;
    el("t_phone_help").textContent = tr.phone_help;
    el("t_submit").textContent = tr.submit;
    el("t_close").textContent = tr.close;
    el("t_footer").textContent = tr.footer;

    langBtn.textContent = lang.toUpperCase();
  }

  function toastMsg(msg) {
    toast.textContent = msg;
    toast.classList.add("show");
    setTimeout(() => toast.classList.remove("show"), 1600);
  }

  function normalizePhoneDigits(v) {
    // keep digits only
    let d = String(v || "").replace(/\D+/g, "");
    // if user typed +998..., keep last 9 digits
    if (d.length > 9) d = d.slice(-9);
    return d;
  }

  function formatPhonePretty(digits) {
    // 901234567 -> 90 123 45 67
    const d = digits.padEnd(9, "");
    return `${d.slice(0,2)} ${d.slice(2,5)} ${d.slice(5,7)} ${d.slice(7,9)}`.trim();
  }

  function validate() {
    const tr = t();
    errName.textContent = "";
    errPhone.textContent = "";

    const name = (fullName.value || "").trim();
    const digits = normalizePhoneDigits(phone.value);

    if (!name) {
      errName.textContent = tr.err_name_required;
      return null;
    }
    if (name.length < 3) {
      errName.textContent = tr.err_name_short;
      return null;
    }
    if (!digits) {
      errPhone.textContent = tr.err_phone_required;
      return null;
    }
    if (digits.length !== 9) {
      errPhone.textContent = tr.err_phone_invalid;
      return null;
    }

    return { full_name: name, phone: `+998${digits}`, phone_digits: digits, lang };
  }

  function setLoading(isLoading) {
    spinner.style.display = isLoading ? "inline-block" : "none";
    submitBtn.disabled = isLoading;
    closeBtn.disabled = isLoading;
  }

  // Phone mask-ish behavior
  phone.addEventListener("input", () => {
    const digits = normalizePhoneDigits(phone.value);
    phone.value = formatPhonePretty(digits);
  });

  // language toggle (UZ -> RU -> EN)
  langBtn.addEventListener("click", () => {
    const order = ["uz", "ru", "en"];
    const idx = order.indexOf(lang);
    lang = order[(idx + 1) % order.length];
    setText();
  });

  closeBtn.addEventListener("click", () => {
    if (tg) tg.close();
    else window.close();
  });

  form.addEventListener("submit", (e) => {
    e.preventDefault();
    const data = validate();
    if (!data) return;

    setLoading(true);
    toastMsg(t().sending);

    const payload = {
      full_name: data.full_name,
      phone: data.phone,
      lang: data.lang
    };

    try {
      if (tg) {
        tg.sendData(JSON.stringify(payload));
        toastMsg(t().sent);
        setTimeout(() => tg.close(), 350);
      } else {
        // fallback for browser test
        console.log("sendData:", payload);
        toastMsg("console.log ✅");
      }
    } finally {
      setTimeout(() => setLoading(false), 450);
    }
  });

  // init
  applyTheme();
  setText();

  // prefill name if available
  if (tg?.initDataUnsafe?.user) {
    const u = tg.initDataUnsafe.user;
    const maybe = [u.first_name, u.last_name].filter(Boolean).join(" ");
    if (maybe && !fullName.value) fullName.value = maybe;
  }
})();