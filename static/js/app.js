document.addEventListener("DOMContentLoaded", () => {

    const logoScreen = document.getElementById("logoScreen");
    const welcomeScreen = document.getElementById("welcomeScreen");

    // انتقال تلقائي من الشعار إلى شاشة الترحيب
    if (logoScreen && welcomeScreen) {
        setTimeout(() => {
            logoScreen.classList.add("hide");
            welcomeScreen.classList.add("show");
        }, 2200);
    }

    // زر ابدأ الآن
    const startButton = document.querySelector(".start-button");

    if (startButton) {
        startButton.addEventListener("click", () => {
            window.location.href = "/home";
        });
    }

});
