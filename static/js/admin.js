if (window.lucide) lucide.createIcons();
document.querySelectorAll(".image-input").forEach((input) => {
  input.addEventListener("change", () => {
    const preview = input.parentElement.querySelector(".preview");
    const file = input.files && input.files[0];
    if (preview && file) preview.src = URL.createObjectURL(file);
  });
});
