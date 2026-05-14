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
  const langSwitcher = el("langSwitcher");

  const I18N = {
    uz: {
      title: "Ro'yxatdan o'tish",
      subtitle: "Ma'lumotlarni kiriting",
      hint: "Bu ma'lumotlar ro'yxatdan o'tishni davom ettirish uchun kerak bo'ladi.",
      name_label: 'Ism familiya',
      name_placeholder: 'Ism familiya',
      phone_label: 'Telefon raqam',
      submit: 'Yuborish',
      close: 'Yopish',
      footer: "Ma’lumotlar xavfsiz saqlanadi.",
      err_name_required: 'Ism familiya kiriting.',
      err_name_short: 'Ism familiya juda qisqa.',
      err_phone_required: 'Telefon raqam kiriting.',
      err_phone_invalid: "9 ta raqam kiriting.",
      sending: 'Yuborilmoqda...',
      sent: 'Yuborildi ✅',
    },
    ru: {
      title: 'Регистрация',
      subtitle: 'Введите данные',
      hint: 'Эти данные нужны, чтобы продолжить регистрацию.',
      name_label: 'Имя и фамилия',
      name_placeholder: 'Имя и фамилия',
      phone_label: 'Телефон',

      submit: 'Отправить',
      close: 'Закрыть',
      footer: 'Данные в безопасности.',
      err_name_required: 'Введите имя и фамилию.',
      err_name_short: 'Слишком коротко.',
      err_phone_required: 'Введите номер телефона.',
      err_phone_invalid: 'Введите 9 цифр.',
      sending: 'Отправка...',
      sent: 'Отправлено ✅',
    },
    en: {
      title: 'Registration',
      subtitle: 'Enter your details',
      hint: 'These details are required to continue registration.',
      name_label: 'Full name',
      name_placeholder: 'Full name',
      phone_label: 'Phone number',
      submit: 'Submit',
      close: 'Close',
      footer: 'Your data is secured.',
      err_name_required: 'Enter your full name.',
      err_name_short: 'Name is too short.',
      err_phone_required: 'Enter your phone number.',
      err_phone_invalid: 'Enter 9 digits.',
      sending: 'Sending...',
      sent: 'Sent ✅',
    },
  };

  function guessLang() {
    const qp = new URLSearchParams(location.search);
    const qLang = (qp.get("lang") || "").toLowerCase();
    if (I18N[qLang]) return qLang;

    const lc = tg?.initDataUnsafe?.user?.language_code;
    if (!lc) return "uz";
    const l = lc.toLowerCase();
    if (l.startsWith("ru")) return "ru";
    if (l.startsWith("en")) return "en";
    return "uz";
  }

  let lang = guessLang();

  function applyTheme() {
    if (!tg) return;
    tg.ready();
    tg.expand();

    // We use our branded theme by default, but we can respect TG colors if needed.
    // For this redesign, we prioritize Sharda University branding.
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
    fullName.placeholder = tr.name_placeholder;
    el("t_phone_label").textContent = tr.phone_label;
    el("t_submit").textContent = tr.submit;
    el("t_close").textContent = tr.close;
    el("t_footer").textContent = tr.footer;

    // Update active state in switcher
    const btns = langSwitcher.querySelectorAll("button");
    btns.forEach(b => {
      if (b.dataset.lang === lang) b.classList.add("active");
      else b.classList.remove("active");
    });
  }

  function toastMsg(msg) {
    toast.textContent = msg;
    toast.classList.add("show");
    setTimeout(() => toast.classList.remove("show"), 2000);
  }

  function normalizePhoneDigits(v) {
    let d = String(v || "").replace(/\D+/g, "");
    if (d.length > 9) d = d.slice(-9);
    return d;
  }

  function formatPhonePretty(digits) {
    const d = digits.padEnd(9, "");
    let res = "";
    if (d.length > 0) res += d.slice(0, 2);
    if (d.length > 2) res += " " + d.slice(2, 5);
    if (d.length > 5) res += " " + d.slice(5, 7);
    if (d.length > 7) res += " " + d.slice(7, 9);
    return res.trim();
  }

  function validate() {
    const tr = t();
    errName.textContent = "";
    errPhone.textContent = "";

    const name = (fullName.value || "").trim();
    const digits = normalizePhoneDigits(phone.value);

    let hasError = false;

    if (!name) {
      errName.textContent = tr.err_name_required;
      hasError = true;
    } else if (name.length < 3) {
      errName.textContent = tr.err_name_short;
      hasError = true;
    }

    if (!digits) {
      errPhone.textContent = tr.err_phone_required;
      hasError = true;
    } else if (digits.length !== 9) {
      errPhone.textContent = tr.err_phone_invalid;
      hasError = true;
    }

    if (hasError) return null;

    return { full_name: name, phone: `+998${digits}`, lang };
  }

  function setLoading(isLoading) {
    spinner.style.display = isLoading ? "inline-block" : "none";
    submitBtn.disabled = isLoading;
    submitBtn.style.opacity = isLoading ? "0.7" : "1";
    closeBtn.disabled = isLoading;
  }

  phone.addEventListener("input", () => {
    const digits = normalizePhoneDigits(phone.value);
    phone.value = formatPhonePretty(digits);
  });

  langSwitcher.addEventListener("click", (e) => {
    const btn = e.target.closest("button");
    if (!btn) return;
    const newLang = btn.dataset.lang;
    if (newLang && I18N[newLang]) {
      lang = newLang;
      setText();
    }
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
        // Note: tg.close() happens after sendData typically
      } else {
        console.log("sendData:", payload);
        setTimeout(() => toastMsg(t().sent), 500);
      }
    } catch (err) {
      console.error(err);
      setLoading(false);
    }
  });

  applyTheme();
  setText();

  if (tg?.initDataUnsafe?.user) {
    const u = tg.initDataUnsafe.user;
    const maybe = [u.first_name, u.last_name].filter(Boolean).join(" ");
    if (maybe && !fullName.value) fullName.value = maybe;
  }
})();
