```javascript
// =========================================================
// CINEMAX — CARRUSELES PC + MÓVIL TÁCTIL
// Series + Terror
// =========================================================


// =========================================================
// CARRUSEL SERIES
// =========================================================

let seriesPosition = 0;

function moveSeries(direction) {

    // En móvil no usamos las flechas.
    // El usuario desliza directamente con el dedo.
    if (window.innerWidth <= 600) {
        return;
    }

    const carousel =
        document.getElementById("seriesCarousel");

    if (!carousel) return;

    const track =
        carousel.querySelector(".carousel-track");

    const cards =
        track.querySelectorAll(".series-card");

    if (!cards.length) return;


    const cardWidth =
        cards[0].offsetWidth + 18;


    const visibleCards =
        Math.floor(
            carousel.offsetWidth / cardWidth
        );


    const maxPosition =
        Math.max(
            0,
            cards.length - visibleCards
        );


    seriesPosition += direction;


    if (seriesPosition < 0) {
        seriesPosition = 0;
    }


    if (seriesPosition > maxPosition) {
        seriesPosition = maxPosition;
    }


    track.style.transform =
        `translateX(-${seriesPosition * cardWidth}px)`;
}


// =========================================================
// CARRUSEL TERROR
// =========================================================

let horrorPosition = 0;

function moveHorror(direction) {

    // En móvil no usamos las flechas.
    if (window.innerWidth <= 600) {
        return;
    }

    const carousel =
        document.getElementById("horrorCarousel");

    if (!carousel) return;

    const track =
        carousel.querySelector(".carousel-track");

    const cards =
        track.querySelectorAll(".horror-card");

    if (!cards.length) return;


    const cardWidth =
        cards[0].offsetWidth + 18;


    const visibleCards =
        Math.floor(
            carousel.offsetWidth / cardWidth
        );


    const maxPosition =
        Math.max(
            0,
            cards.length - visibleCards
        );


    horrorPosition += direction;


    if (horrorPosition < 0) {
        horrorPosition = 0;
    }


    if (horrorPosition > maxPosition) {
        horrorPosition = maxPosition;
    }


    track.style.transform =
        `translateX(-${horrorPosition * cardWidth}px)`;
}


// =========================================================
// SWIPE TÁCTIL — SERIES
// =========================================================

const seriesCarousel =
    document.getElementById("seriesCarousel");

if (seriesCarousel) {

    let startX = 0;
    let startY = 0;


    seriesCarousel.addEventListener(
        "touchstart",
        function (e) {

            startX =
                e.touches[0].clientX;

            startY =
                e.touches[0].clientY;

        },
        { passive: true }
    );


    seriesCarousel.addEventListener(
        "touchend",
        function (e) {

            const endX =
                e.changedTouches[0].clientX;

            const endY =
                e.changedTouches[0].clientY;


            const differenceX =
                startX - endX;

            const differenceY =
                startY - endY;


            // Solo actuamos si el movimiento
            // fue principalmente horizontal.
            if (
                Math.abs(differenceX) >
                Math.abs(differenceY)
            ) {

                // Deslizar hacia la izquierda
                if (differenceX > 50) {

                    seriesCarousel.scrollBy({
                        left: 180,
                        behavior: "smooth"
                    });

                }


                // Deslizar hacia la derecha
                if (differenceX < -50) {

                    seriesCarousel.scrollBy({
                        left: -180,
                        behavior: "smooth"
                    });

                }

            }

        },
        { passive: true }
    );
}


// =========================================================
// SWIPE TÁCTIL — TERROR
// =========================================================

const horrorCarousel =
    document.getElementById("horrorCarousel");

if (horrorCarousel) {

    let startX = 0;
    let startY = 0;


    horrorCarousel.addEventListener(
        "touchstart",
        function (e) {

            startX =
                e.touches[0].clientX;

            startY =
                e.touches[0].clientY;

        },
        { passive: true }
    );


    horrorCarousel.addEventListener(
        "touchend",
        function (e) {

            const endX =
                e.changedTouches[0].clientX;

            const endY =
                e.changedTouches[0].clientY;


            const differenceX =
                startX - endX;

            const differenceY =
                startY - endY;


            if (
                Math.abs(differenceX) >
                Math.abs(differenceY)
            ) {

                // Izquierda
                if (differenceX > 50) {

                    horrorCarousel.scrollBy({
                        left: 190,
                        behavior: "smooth"
                    });

                }


                // Derecha
                if (differenceX < -50) {

                    horrorCarousel.scrollBy({
                        left: -190,
                        behavior: "smooth"
                    });

                }

            }

        },
        { passive: true }
    );
}


// =========================================================
// REAJUSTAR AL CAMBIAR TAMAÑO
// =========================================================

window.addEventListener(
    "resize",
    function () {

        if (window.innerWidth > 600) {

            seriesPosition = 0;
            horrorPosition = 0;


            const seriesTrack =
                document.querySelector(
                    "#seriesCarousel .carousel-track"
                );


            const horrorTrack =
                document.querySelector(
                    "#horrorCarousel .carousel-track"
                );


            if (seriesTrack) {

                seriesTrack.style.transform =
                    "translateX(0)";
            }


            if (horrorTrack) {

                horrorTrack.style.transform =
                    "translateX(0)";
            }

        } else {

            // En móvil quitamos cualquier
            // transform que haya dejado el PC.

            const seriesTrack =
                document.querySelector(
                    "#seriesCarousel .carousel-track"
                );


            const horrorTrack =
                document.querySelector(
                    "#horrorCarousel .carousel-track"
                );


            if (seriesTrack) {

                seriesTrack.style.transform =
                    "none";
            }


            if (horrorTrack) {

                horrorTrack.style.transform =
                    "none";
            }

        }

    }
);
```


