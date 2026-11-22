import { h } from "../utils/dom.js";
import { api, session } from "../services/api.js";

export function AuthView({ onSuccess }) {
  const root = h("section", { class: "auth" });
  let mode = "login";

  function field(id, label, attrs = {}) {
    const input = h("input", { id, name: id, required: true, ...attrs });
    return { input, node: h("div", { class: "field" }, h("label", { for: id }, label), input) };
  }

  function render() {
    const isLogin = mode === "login";
    const error = h("p", { class: "form-error", role: "alert", hidden: true });
    const username = field("username", "Логин", {
      autocomplete: "username", autocapitalize: "none", spellcheck: "false",
    });
    const password = field("password", "Пароль", {
      type: "password", autocomplete: isLogin ? "current-password" : "new-password",
    });
    const fullName = field("full_name", "Имя и фамилия", { autocomplete: "name", required: false });
    const submit = h("button", { class: "btn primary", type: "submit" },
      isLogin ? "Войти" : "Создать аккаунт");

    const form = h("form", {
      novalidate: true,
      onsubmit: async (event) => {
        event.preventDefault();
        error.hidden = true;
        submit.disabled = true;
        try {
          const credentials = {
            username: username.input.value.trim(),
            password: password.input.value,
          };
          if (!isLogin) {
            await api.register({ ...credentials, full_name: fullName.input.value.trim() });
          }
          const { access_token } = await api.login(credentials);
          session.save(access_token);
          await onSuccess();
        } catch (err) {
          error.textContent = err.message;
          error.hidden = false;
          submit.disabled = false;
        }
      },
    },
      username.node,
      isLogin ? null : fullName.node,
      password.node,
      error,
      submit,
    );

    const toggle = h("button", {
      class: "link-button", type: "button",
      onclick: () => { mode = isLogin ? "register" : "login"; render(); },
    }, isLogin ? "У меня нет аккаунта" : "У меня уже есть аккаунт");

    const demo = isLogin ? h("div", { class: "demo" },
      h("p", {}, "Демо-доступ для проверки:"),
      h("div", { class: "demo-actions" },
        demoButton("Сотрудник", "demo", "demo123"),
        demoButton("Поддержка", "agent", "agent123"),
      ),
    ) : null;

    function demoButton(label, login, pass) {
      return h("button", {
        class: "btn ghost", type: "button",
        onclick: () => { username.input.value = login; password.input.value = pass; submit.click(); },
      }, label);
    }

    root.replaceChildren(
      h("h1", {}, isLogin ? "Вход в систему заявок" : "Новый аккаунт"),
      h("p", { class: "lead" }, isLogin
        ? "Опишите проблему с техникой или доступом, и поддержка возьмёт её в работу."
        : "Логин: от 3 символов, латиница, цифры, точка, дефис. Пароль: от 6 символов."),
      form,
      toggle,
      demo,
    );
    username.input.focus();
  }

  render();
  return root;
}
