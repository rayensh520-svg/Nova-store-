function toggleTheme() {
    document.body.classList.toggle("dark");

    const isDark = document.body.classList.contains("dark");

    localStorage.setItem(
        "dzmarket-theme",
        isDark ? "dark" : "light"
    );

    const button = document.querySelector(
        '[title="الوضع الليلي"], [title="الوضع النهاري"]'
    );

    if (button) {
        button.textContent = isDark ? "☀️" : "🌙";
        button.title = isDark ? "الوضع النهاري" : "الوضع الليلي";
    }
}


document.addEventListener("DOMContentLoaded", () => {

    // تحميل الوضع المحفوظ
    const savedTheme = localStorage.getItem("dzmarket-theme");

    if (savedTheme === "dark") {
        document.body.classList.add("dark");
    }

    // تحديث زر الوضع الليلي
    const button = document.querySelector(
        '[title="الوضع الليلي"], [title="الوضع النهاري"]'
    );

    if (button) {
        const isDark = document.body.classList.contains("dark");

        button.textContent = isDark ? "☀️" : "🌙";
        button.title = isDark
            ? "الوضع النهاري"
            : "الوضع الليلي";
    }

    // أزرار المفضلة
    document.querySelectorAll(".favorite").forEach((button) => {

        button.addEventListener("click", () => {

            button.classList.toggle("active");

            button.textContent =
                button.classList.contains("active")
                    ? "♥"
                    : "♡";
        });

    });

});
