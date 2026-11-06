// Inicializa los carruseles: avance automático, pausa y preferencia de movimiento reducido.
(function () {
    const INTERVALO_MS = 5000;
    const reducirMovimiento = window.matchMedia(
        "(prefers-reduced-motion: reduce)"
    ).matches;

    function iniciarCarruselAutomatico(elemento) {
        const carrusel = bootstrap.Carousel.getOrCreateInstance(elemento, {
            interval: INTERVALO_MS,
            ride: false,
            pause: false,
        });
        const boton = elemento.querySelector("[data-carrusel-pausa]");

        // Si el usuario pide reducir el movimiento, el carrusel parte detenido.
        let pausado = reducirMovimiento;

        function reanudar() {
            if (!pausado) {
                carrusel.cycle();
            }
        }

        function actualizarBoton() {
            boton.setAttribute(
                "aria-label",
                pausado ? "Reanudar carrusel" : "Pausar carrusel"
            );
            boton.querySelector("[data-icono-pausa]").hidden = pausado;
            boton.querySelector("[data-icono-reanudar]").hidden = !pausado;
        }

        // Se detiene mientras el usuario lo mira o navega por él con el teclado.
        elemento.addEventListener("mouseenter", () => carrusel.pause());
        elemento.addEventListener("mouseleave", reanudar);
        elemento.addEventListener("focusin", () => carrusel.pause());
        elemento.addEventListener("focusout", reanudar);

        boton.addEventListener("click", () => {
            pausado = !pausado;

            if (pausado) {
                carrusel.pause();
            } else {
                carrusel.cycle();
            }

            actualizarBoton();
        });

        actualizarBoton();
        reanudar();
    }

    document
        .querySelectorAll("[data-carrusel-automatico]")
        .forEach(iniciarCarruselAutomatico);

    // Crear la instancia desde el inicio habilita el gesto táctil y el teclado.
    document
        .querySelectorAll(".carousel:not([data-carrusel-automatico])")
        .forEach((elemento) => {
            bootstrap.Carousel.getOrCreateInstance(elemento, {
                interval: false,
                ride: false,
            });
        });
})();
