const canvas = document.querySelector("#drawing-canvas");

if (canvas) {
	const context = canvas.getContext("2d");
	const colorInput = document.querySelector("#brush-color");
	const sizeInput = document.querySelector("#brush-size");
	const sizeOutput = document.querySelector("#brush-size-value");
	const clearButton = document.querySelector("#clear-canvas");
	const eraserButton = document.querySelector("#eraser-tool");
	const fileInput = document.querySelector("#imagem");
	const preview = document.querySelector("#image-preview");
	const hint = document.querySelector("#canvas-hint");
	const uploadName = document.querySelector("#upload-name");
	const form = document.querySelector("#artwork-form");
	let drawing = false;
	let hasDrawing = false;
	let erasing = false;

	context.lineCap = "round";
	context.lineJoin = "round";

	canvas.addEventListener("pointerdown", (event) => {
		if (fileInput.files.length) return;
		drawing = true;
		hasDrawing = true;
		canvas.setPointerCapture(event.pointerId);
		const bounds = canvas.getBoundingClientRect();
		context.beginPath();
		context.moveTo((event.clientX - bounds.left) * canvas.width / bounds.width, (event.clientY - bounds.top) * canvas.height / bounds.height);
		hint.hidden = true;
	});

	canvas.addEventListener("pointermove", (event) => {
		if (!drawing) return;
		const bounds = canvas.getBoundingClientRect();
		context.globalCompositeOperation = erasing ? "destination-out" : "source-over";
		context.strokeStyle = erasing ? "rgba(0, 0, 0, 1)" : colorInput.value;
		context.lineWidth = Number(sizeInput.value) * canvas.width / bounds.width;
		context.lineTo((event.clientX - bounds.left) * canvas.width / bounds.width, (event.clientY - bounds.top) * canvas.height / bounds.height);
		context.stroke();
	});

	const stopDrawing = () => { drawing = false; };
	canvas.addEventListener("pointerup", stopDrawing);
	canvas.addEventListener("pointercancel", stopDrawing);
	canvas.addEventListener("pointerleave", stopDrawing);

	sizeInput.addEventListener("input", () => { sizeOutput.value = sizeInput.value; });

	clearButton.addEventListener("click", () => {
		context.clearRect(0, 0, canvas.width, canvas.height);
		hasDrawing = false;
		hint.hidden = false;
	});

	eraserButton.addEventListener("click", () => {
		erasing = !erasing;
		eraserButton.setAttribute("aria-pressed", String(erasing));
		eraserButton.classList.toggle("is-active", erasing);
	});

	fileInput.addEventListener("change", () => {
		const file = fileInput.files[0];
		if (!file) {
			preview.hidden = true;
			canvas.hidden = false;
			uploadName.textContent = "PNG, JPG ou GIF · até 16 MB";
			return;
		}
		uploadName.textContent = file.name;
		const imageUrl = URL.createObjectURL(file);
		preview.onload = () => URL.revokeObjectURL(imageUrl);
		preview.src = imageUrl;
		preview.hidden = false;
		canvas.hidden = true;
		hint.hidden = true;
	});

	form.addEventListener("submit", (event) => {
		if (!fileInput.files.length && hasDrawing) {
			document.querySelector("#desenho-canvas").value = canvas.toDataURL("image/png");
		} else if (!fileInput.files.length) {
			event.preventDefault();
			hint.textContent = "Faça um desenho ou escolha uma imagem para publicar";
			hint.hidden = false;
			canvas.focus();
		}
	});
}
