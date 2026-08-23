/* =========================================================
   CINEMAX — JAVASCRIPT COMPLETO
   =========================================================
   FUNCIONES:

   - Login / sesión
   - Catálogo
   - Películas
   - Series
   - Terror
   - Agregar contenido
   - Editar contenido
   - Eliminar contenido
   - Papelera
   - Restaurar
   - Eliminación permanente
   - Temporadas
   - Episodios
   - Usuarios
   - Dashboard
   - Estadísticas
   - Actualización automática
   - Comprobación de sesión

   CORRECCIÓN PRINCIPAL:

   Terror se detecta correctamente aunque venga como:

   category: "terror"
   type: "terror"
   genre: "terror"
   genre: "Terror"
   genre: ["Terror"]
   genres: ["Terror"]
   genres: [{ name: "Terror" }]
   genres: [{ title: "Terror" }]
   category: "pelicula" + genre "Terror"
   category: "movie" + genre "Horror"

   TERROR tiene prioridad sobre PELÍCULA.

   SERIES mantiene prioridad sobre un género Terror/Horror,
   porque una serie de terror debe seguir siendo una serie.

========================================================= */


/* =========================================================
   CONFIGURACIÓN
========================================================= */

const API_URL = "";


/* =========================================================
   ESTADO GLOBAL
========================================================= */

let sessionId =
    localStorage.getItem(
        "cinemax_session_id"
    );

let currentUser = null;

let catalog = [];

let trash = [];

let users = [];


/* =========================================================
   ESTADO SERIES / EPISODIOS
========================================================= */

let episodesSeries = [];

let editingSeriesId = null;

let editingSeries = null;

let editingSeasons = [];


/* =========================================================
   UTILIDADES DOM
========================================================= */

function $(id) {

    return document.getElementById(id);

}


function setValue(id, value) {

    const element = $(id);

    if (element) {

        element.value =
            value ?? "";

    }

}


function getValue(id) {

    const element = $(id);

    return element
        ? element.value
        : "";

}


function setText(id, value) {

    const element = $(id);

    if (element) {

        element.textContent =
            value ?? "";

    }

}


/* =========================================================
   IDENTIFICADOR RESISTENTE
========================================================= */

function getContentId(item) {

    if (
        !item ||
        typeof item !== "object"
    ) {

        return "";

    }


    const possibleIds = [

        item.id,
        item._id,
        item.content_id,
        item.contentId,
        item.catalog_id,
        item.catalogId,
        item.uuid,
        item.ID

    ];


    for (
        const value of possibleIds
    ) {

        if (
            value !== undefined &&
            value !== null &&
            String(value).trim() !== ""
        ) {

            return String(value);

        }

    }


    return "";

}


/* =========================================================
   BUSCAR CONTENIDO POR ID
========================================================= */

function findCatalogItemById(id) {

    if (
        id === undefined ||
        id === null
    ) {

        return null;

    }


    const target =
        String(id);


    return (
        catalog.find(
            item =>
                getContentId(item) === target
        )
    ) || null;

}


/* =========================================================
   EXTRAER OBJETO CREADO / ACTUALIZADO
========================================================= */

function extractCatalogItem(response) {

    if (
        !response ||
        typeof response !== "object"
    ) {

        return null;

    }


    const candidates = [

        response.data,
        response.item,
        response.content,
        response.catalog,
        response.result,
        response.created,
        response.createdItem,
        response.updated,
        response.updatedItem

    ];


    for (
        const candidate of candidates
    ) {

        if (
            candidate &&
            typeof candidate === "object" &&
            !Array.isArray(candidate)
        ) {

            const id =
                getContentId(candidate);


            if (id) {

                return candidate;

            }

        }

    }


    if (
        getContentId(response)
    ) {

        return response;

    }


    return null;

}


/* =========================================================
   NORMALIZAR TEXTO
========================================================= */

function normalizeText(value) {

    if (
        value === undefined ||
        value === null
    ) {

        return "";

    }


    /*
       Si llega un objeto, intentamos sacar
       sus propiedades habituales.
    */

    if (
        typeof value === "object" &&
        !Array.isArray(value)
    ) {

        value =
            value.name ??
            value.title ??
            value.label ??
            value.value ??
            value.genre ??
            value.category ??
            value.type ??
            "";

    }


    return String(value)
        .trim()
        .toLowerCase()
        .normalize("NFD")
        .replace(
            /[\u0300-\u036f]/g,
            ""
        );

}


/* =========================================================
   OBTENER TODOS LOS VALORES DE GÉNERO
========================================================= */

function getAllGenres(item) {

    if (
        !item ||
        typeof item !== "object"
    ) {

        return [];

    }


    const result = [];


    /*
       -----------------------------------------------------
       genre
       -----------------------------------------------------
    */

    if (
        Array.isArray(item.genre)
    ) {

        result.push(
            ...item.genre
        );

    }

    else if (
        item.genre !== undefined &&
        item.genre !== null
    ) {

        result.push(
            item.genre
        );

    }


    /*
       -----------------------------------------------------
       genres
       -----------------------------------------------------
    */

    if (
        Array.isArray(item.genres)
    ) {

        result.push(
            ...item.genres
        );

    }

    else if (
        item.genres !== undefined &&
        item.genres !== null
    ) {

        result.push(
            item.genres
        );

    }


    /*
       -----------------------------------------------------
       tags
       -----------------------------------------------------
    */

    if (
        Array.isArray(item.tags)
    ) {

        result.push(
            ...item.tags
        );

    }

    else if (
        item.tags !== undefined &&
        item.tags !== null
    ) {

        result.push(
            item.tags
        );

    }


    /*
       -----------------------------------------------------
       Convertir todos los valores a texto
       -----------------------------------------------------
    */

    const normalized = [];


    function addValue(value) {

        if (
            value === undefined ||
            value === null
        ) {

            return;

        }


        /*
           Objetos como:

           {name:"Terror"}

           {title:"Terror"}

           {label:"Terror"}
        */

        if (
            typeof value === "object" &&
            !Array.isArray(value)
        ) {

            const possible = [

                value.name,
                value.title,
                value.label,
                value.value,
                value.genre,
                value.category,
                value.type

            ];


            possible.forEach(
                candidate => {

                    if (
                        candidate !== undefined &&
                        candidate !== null
                    ) {

                        addValue(
                            candidate
                        );

                    }

                }
            );


            return;

        }


        /*
           Arrays anidados
        */

        if (
            Array.isArray(value)
        ) {

            value.forEach(
                addValue
            );

            return;

        }


        /*
           Strings con múltiples géneros
        */

        const text =
            String(value);


        text
            .split(
                /[,|/;]+/
            )
            .forEach(
                part => {

                    const clean =
                        normalizeText(
                            part
                        );


                    if (clean) {

                        normalized.push(
                            clean
                        );

                    }

                }
            );

    }


    result.forEach(
        addValue
    );


    return normalized;

}


/* =========================================================
   ¿ES TERROR?
========================================================= */

function isTerrorContent(item) {

    if (
        !item ||
        typeof item !== "object"
    ) {

        return false;

    }


    /*
       -----------------------------------------------------
       CATEGORY
       -----------------------------------------------------
    */

    const categoryValues = [

        item.category,
        item.type,
        item.contentType,
        item.content_type

    ];


    for (
        const value of categoryValues
    ) {

        const normalized =
            normalizeText(
                value
            );


        if (

            normalized === "terror" ||

            normalized === "horror" ||

            normalized === "horrors" ||

            normalized.includes("terror") ||

            normalized.includes("horror")

        ) {

            return true;

        }

    }


    /*
       -----------------------------------------------------
       GÉNEROS
       -----------------------------------------------------
    */

    const genres =
        getAllGenres(
            item
        );


    return genres.some(
        genre => {

            const text =
                normalizeText(
                    genre
                );


            return (

                text === "terror" ||

                text === "horror" ||

                text.includes("terror") ||

                text.includes("horror")

            );

        }
    );

}


/* =========================================================
   ¿ES SERIE?
========================================================= */

function isSeriesContent(item) {

    if (
        !item ||
        typeof item !== "object"
    ) {

        return false;

    }


    const values = [

        item.category,
        item.type,
        item.contentType,
        item.content_type

    ];


    for (
        const value of values
    ) {

        const text =
            normalizeText(
                value
            );


        if (

            text === "serie" ||

            text === "series" ||

            text === "tv" ||

            text === "show" ||

            text === "shows" ||

            text === "tvshow" ||

            text === "tv show"

        ) {

            return true;

        }

    }


    /*
       Si tiene temporadas también lo consideramos serie.
    */

    if (
        Array.isArray(
            item.seasons
        )
    ) {

        return true;

    }


    return false;

}


/* =========================================================
   NORMALIZAR CATEGORÍA
========================================================= */

function normalizeCategory(value) {

    const text =
        normalizeText(
            value
        );


    if (

        text === "terror" ||

        text === "horror" ||

        text === "horrors"

    ) {

        return "terror";

    }


    if (

        text === "tv" ||

        text === "show" ||

        text === "shows" ||

        text === "serie" ||

        text === "series" ||

        text === "tvshow" ||

        text === "tv show"

    ) {

        return "serie";

    }


    if (

        text === "movie" ||

        text === "movies" ||

        text === "pelicula" ||

        text === "peliculas" ||

        text === "film" ||

        text === "films"

    ) {

        return "pelicula";

    }


    return text ||
        "pelicula";

}


/* =========================================================
   DETECTAR CATEGORÍA REAL
========================================================= */

function getRealCategory(item) {

    if (
        !item ||
        typeof item !== "object"
    ) {

        return "pelicula";

    }


    /*
       =====================================================
       1. TERROR EXPLÍCITO
       =====================================================
    */

    const explicitCategory =
        normalizeCategory(
            item.category ||
            ""
        );


    const explicitType =
        normalizeCategory(
            item.type ||
            ""
        );


    /*
       Si category o type dicen explícitamente terror,
       es terror.
    */

    if (
        explicitCategory === "terror" ||
        explicitType === "terror"
    ) {

        return "terror";

    }


    /*
       =====================================================
       2. SERIES
       =====================================================
    */

    /*
       IMPORTANTE:

       Una serie con género Terror sigue siendo SERIE.

       Ejemplo:

       category: "serie"
       genre: "Terror"

       Resultado:

       serie
    */

    if (
        isSeriesContent(item)
    ) {

        return "serie";

    }


    /*
       =====================================================
       3. TERROR POR GÉNERO
       =====================================================
    */

    if (
        isTerrorContent(item)
    ) {

        return "terror";

    }


    /*
       =====================================================
       4. PELÍCULA
       =====================================================
    */

    if (
        explicitCategory === "pelicula"
    ) {

        return "pelicula";

    }


    if (
        explicitType === "pelicula"
    ) {

        return "pelicula";

    }


    /*
       =====================================================
       5. CUALQUIER OTRA VARIANTE
       =====================================================
    */

    const fallback =
        normalizeCategory(
            item.category ||
            item.type ||
            ""
        );


    return fallback ||
        "pelicula";

}


/* =========================================================
   DEBUG DE CATEGORÍAS
========================================================= */

function debugCatalogCategories() {

    console.log(
        "=============================================="
    );

    console.log(
        "🎬 CINEMAX — CLASIFICACIÓN DEL CATÁLOGO"
    );

    console.log(
        "=============================================="
    );


    let movies = 0;

    let series = 0;

    let terror = 0;


    catalog.forEach(
        item => {

            const category =
                getRealCategory(
                    item
                );


            if (
                category === "pelicula"
            ) {

                movies++;

            }

            else if (
                category === "serie"
            ) {

                series++;

            }

            else if (
                category === "terror"
            ) {

                terror++;

            }


            console.log({

                id:
                    getContentId(
                        item
                    ),

                title:
                    item.title ||
                    item.name,

                category:
                    item.category,

                type:
                    item.type,

                genre:
                    item.genre,

                genres:
                    item.genres,

                tags:
                    item.tags,

                detected:
                    category

            });

        }
    );


    console.log(
        "----------------------------------------------"
    );

    console.log(
        "🎬 Películas:",
        movies
    );

    console.log(
        "📺 Series:",
        series
    );

    console.log(
        "👻 Terror:",
        terror
    );

    console.log(
        "📦 Total:",
        catalog.length
    );

    console.log(
        "=============================================="
    );

}


/* =========================================================
   API PRINCIPAL
========================================================= */

async function api(
    endpoint,
    options = {}
) {

    const headers = {

        "Content-Type":
            "application/json",

        ...(options.headers || {})

    };


    /*
       Compatibilidad de sesión
    */

    if (sessionId) {

        headers["X-Session-ID"] =
            sessionId;

        headers["Authorization"] =
            "Bearer " +
            sessionId;

    }


    const config = {

        ...options,

        headers

    };


    /*
       Agregar session_id al body
    */

    if (

        config.body &&

        typeof config.body ===
        "string"

    ) {

        try {

            const body =
                JSON.parse(
                    config.body
                );


            if (
                sessionId &&
                !body.session_id
            ) {

                body.session_id =
                    sessionId;


                config.body =
                    JSON.stringify(
                        body
                    );

            }

        } catch (_) {}

    }


    const response =
        await fetch(
            API_URL + endpoint,
            config
        );


    let data = null;


    try {

        data =
            await response.json();

    }

    catch (_) {

        data = {

            success: false,

            error:
                "Respuesta inválida del servidor."

        };

    }


    /*
       SESIÓN EXPIRADA
    */

    if (
        response.status === 401
    ) {

        localStorage.removeItem(
            "cinemax_session_id"
        );


        sessionId = null;

        currentUser = null;


        showLogin(
            data?.error ||
            "Sesión expirada."
        );


        throw new Error(
            data?.error ||
            "Sesión expirada."
        );

    }


    /*
       ACCESO DENEGADO
    */

    if (
        response.status === 403
    ) {

        throw new Error(
            data?.error ||
            "Acceso denegado."
        );

    }


    /*
       OTROS ERRORES
    */

    if (
        !response.ok
    ) {

        throw new Error(
            data?.error ||
            data?.message ||
            "Error en la solicitud."
        );

    }


    return data;

}


/* =========================================================
   INICIO
========================================================= */

document.addEventListener(
    "DOMContentLoaded",
    init
);


async function init() {

    if (!sessionId) {

        showLogin();

        return;

    }


    try {

        const response =
            await fetch(

                API_URL +
                "/api/users/session/" +
                encodeURIComponent(
                    sessionId
                ),

                {

                    method:
                        "GET",

                    headers: {

                        "Content-Type":
                            "application/json",

                        "X-Session-ID":
                            sessionId,

                        "Authorization":
                            "Bearer " +
                            sessionId

                    }

                }

            );


        const result =
            await response.json();


        if (

            !result.success ||

            !result.active

        ) {

            localStorage.removeItem(
                "cinemax_session_id"
            );


            sessionId = null;

            currentUser = null;


            showLogin();

            return;

        }


        /*
           SOLO ADMIN
        */

        if (

            String(
                result.user?.role ||
                "user"
            ).toLowerCase()
            !==
            "admin"

        ) {

            localStorage.removeItem(
                "cinemax_session_id"
            );


            sessionId = null;

            currentUser = null;


            showLogin(
                "Esta cuenta no tiene permisos de administrador."
            );


            return;

        }


        currentUser =
            result.user;


        showApp();

        await loadAll();


    }

    catch (error) {

        console.error(
            "ERROR COMPROBANDO SESIÓN:",
            error
        );


        localStorage.removeItem(
            "cinemax_session_id"
        );


        sessionId = null;

        currentUser = null;


        showLogin(
            "No se pudo comprobar la sesión."
        );

    }

}


/* =========================================================
   LOGIN
========================================================= */

function initializeLoginForm() {

    const form =
        $("loginForm");


    if (!form) {

        return;

    }


    if (
        form.dataset.initialized ===
        "true"
    ) {

        return;

    }


    form.dataset.initialized =
        "true";


    form.addEventListener(
        "submit",
        async function(event) {

            event.preventDefault();


            const email =
                getValue(
                    "loginEmail"
                ).trim();


            const password =
                getValue(
                    "loginPassword"
                );


            const errorBox =
                $("loginError");


            if (errorBox) {

                errorBox.style.display =
                    "none";

            }


            try {

                const result =
                    await fetch(

                        API_URL +
                        "/api/users/login",

                        {

                            method:
                                "POST",

                            headers: {

                                "Content-Type":
                                    "application/json"

                            },

                            body:
                                JSON.stringify({

                                    email,

                                    password

                                })

                        }

                    );


                const data =
                    await result.json();


                if (
                    !result.ok
                ) {

                    throw new Error(
                        data?.error ||
                        "Error al iniciar sesión."
                    );

                }


                const receivedSession =

                    data.session_id ||

                    data.sessionId ||

                    data.session ||

                    data.token;


                if (
                    !receivedSession
                ) {

                    throw new Error(
                        "El servidor inició sesión, pero no devolvió el ID de sesión."
                    );

                }


                if (

                    String(
                        data.user?.role ||
                        "user"
                    ).toLowerCase()
                    !==
                    "admin"

                ) {

                    throw new Error(
                        "Esta cuenta no tiene permisos de administrador."
                    );

                }


                sessionId =
                    receivedSession;


                currentUser =
                    data.user;


                localStorage.setItem(
                    "cinemax_session_id",
                    sessionId
                );


                showApp();


                await loadAll();


                showToast(
                    "Sesión de administrador iniciada.",
                    "success"
                );

            }

            catch (error) {

                console.error(
                    "LOGIN ERROR:",
                    error
                );


                if (errorBox) {

                    errorBox.textContent =
                        error.message;


                    errorBox.style.display =
                        "block";

                }

            }

        }
    );

}


document.addEventListener(
    "DOMContentLoaded",
    initializeLoginForm
);


/* =========================================================
   MOSTRAR LOGIN
========================================================= */

function showLogin(
    message = ""
) {

    const loading =
        $("loadingScreen");


    const app =
        $("app");


    const login =
        $("loginScreen");


    if (loading) {

        loading.style.display =
            "none";

    }


    if (app) {

        app.style.display =
            "none";

    }


    if (login) {

        login.style.display =
            "flex";

    }


    if (message) {

        const errorBox =
            $("loginError");


        if (errorBox) {

            errorBox.textContent =
                message;


            errorBox.style.display =
                "block";

        }

    }

}


/* =========================================================
   MOSTRAR APP
========================================================= */

function showApp() {

    const loading =
        $("loadingScreen");


    const login =
        $("loginScreen");


    const app =
        $("app");


    if (loading) {

        loading.style.display =
            "none";

    }


    if (login) {

        login.style.display =
            "none";

    }


    if (app) {

        app.style.display =
            "block";

    }


    if (currentUser) {

        setText(
            "topUsername",
            currentUser.username ||
            "Administrador"
        );


        setText(
            "topEmail",
            currentUser.email ||
            ""
        );

    }

}


/* =========================================================
   LOGOUT
========================================================= */

async function logout() {

    if (!sessionId) {

        showLogin();

        return;

    }


    try {

        await api(
            "/api/users/logout",
            {

                method:
                    "POST",

                body:
                    JSON.stringify({})

            }
        );

    }

    catch (_) {}


    localStorage.removeItem(
        "cinemax_session_id"
    );


    sessionId = null;

    currentUser = null;

    catalog = [];

    trash = [];

    users = [];

    episodesSeries = [];

    editingSeriesId = null;

    editingSeries = null;

    editingSeasons = [];


    showLogin();

}


/* =========================================================
   NAVEGACIÓN
========================================================= */

function showSection(
    section,
    button
) {

    document
        .querySelectorAll(
            ".section"
        )
        .forEach(
            element =>
                element.classList.remove(
                    "active"
                )
        );


    const target =
        $("section-" + section);


    if (target) {

        target.classList.add(
            "active"
        );

    }


    document
        .querySelectorAll(
            ".nav-btn"
        )
        .forEach(
            element =>
                element.classList.remove(
                    "active"
                )
        );


    if (button) {

        button.classList.add(
            "active"
        );

    }

    else {

        const nav =
            document.querySelector(
                `[data-section="${section}"]`
            );


        if (nav) {

            nav.classList.add(
                "active"
            );

        }

    }


    if (
        section === "catalog"
    ) {

        renderCatalog();

    }


    if (
        section === "episodes"
    ) {

        loadEpisodesSeries();

    }


    if (
        section === "trash"
    ) {

        loadTrash();

    }


    if (
        section === "users"
    ) {

        loadUsers();

    }


    if (
        section === "dashboard"
    ) {

        updateStats();

        renderDashboard();

    }

}


/* =========================================================
   CARGAR TODO
========================================================= */

async function loadAll() {

    await Promise.allSettled([

        loadCatalog(),

        loadUsers(),

        loadTrash()

    ]);


    updateStats();

    renderDashboard();

    loadEpisodesSeries();

}


/* =========================================================
   EXTRAER ARRAY DE CATÁLOGO
========================================================= */

function extractCatalogArray(response) {

    if (
        Array.isArray(response)
    ) {

        return response;

    }


    const candidates = [

        response?.data,
        response?.catalog,
        response?.items,
        response?.contents,
        response?.results

    ];


    for (
        const candidate of candidates
    ) {

        if (
            Array.isArray(candidate)
        ) {

            return candidate;

        }

    }


    return [];

}


/* =========================================================
   CATÁLOGO — CARGAR
========================================================= */

async function loadCatalog() {

    try {

        const response =
            await api(
                "/api/catalog"
            );


        catalog =
            extractCatalogArray(
                response
            );


        console.log(
            "=============================================="
        );

        console.log(
            "📚 CATÁLOGO CARGADO"
        );

        console.log(
            "Total registros:",
            catalog.length
        );


        /*
           DEBUG DE CATEGORÍAS
        */

        debugCatalogCategories();


        /*
           Renderizar todo
        */

        renderCatalog();

        updateStats();

        renderDashboard();

        loadEpisodesSeries();


    }

    catch (error) {

        console.error(
            "ERROR CARGANDO CATÁLOGO:",
            error
        );


        showToast(
            error.message,
            "error"
        );

    }

}


/* =========================================================
   RENDER CATÁLOGO
========================================================= */

function renderCatalog() {

    const table =
        $("catalogTable");


    if (!table) {

        console.warn(
            "No existe #catalogTable en el HTML."
        );

        return;

    }


    const search =
        getValue(
            "catalogSearch"
        )
        .trim()
        .toLowerCase();


    const filter =
        normalizeText(
            getValue(
                "catalogFilter"
            )
        ) ||
        "all";


    const filtered =
        catalog.filter(
            item => {

                const title =
                    String(
                        item.title ||
                        item.name ||
                        ""
                    ).toLowerCase();


                const id =
                    getContentId(
                        item
                    ).toLowerCase();


                const category =
                    getRealCategory(
                        item
                    );


                const genreText =
                    getAllGenres(
                        item
                    ).join(" ");


                const matchesSearch =

                    !search ||

                    title.includes(
                        search
                    ) ||

                    id.includes(
                        search
                    ) ||

                    category.includes(
                        search
                    ) ||

                    genreText.includes(
                        search
                    );


                const matchesFilter =

                    filter === "all" ||

                    filter === "todas" ||

                    category === filter;


                return (

                    matchesSearch &&

                    matchesFilter

                );

            }
        );


    /*
       Actualizar contador si existe
    */

    updateCatalogCounter(
        filtered
    );


    if (!filtered.length) {

        table.innerHTML = `

            <tr>

                <td colspan="5">

                    <div class="empty">

                        No hay contenido que mostrar.

                    </div>

                </td>

            </tr>

        `;

        return;

    }


    table.innerHTML =
        filtered
            .map(
                item => {

                    const itemId =
                        getContentId(
                            item
                        );


                    const id =
                        escapeHtml(
                            itemId
                        );


                    const title =
                        escapeHtml(
                            item.title ||
                            item.name ||
                            "Sin título"
                        );


                    const category =
                        getRealCategory(
                            item
                        );


                    const year =
                        escapeHtml(
                            item.year ||
                            "-"
                        );


                    return `

                        <tr>

                            <td>

                                <strong>
                                    ${title}
                                </strong>

                            </td>


                            <td>

                                ${categoryBadge(
                                    category
                                )}

                            </td>


                            <td>

                                ${year}

                            </td>


                            <td>

                                <code>
                                    ${id}
                                </code>

                            </td>


                            <td>

                                <div
                                    class="actions"
                                    style="
                                        display:flex;
                                        flex-wrap:wrap;
                                        gap:6px;
                                    "
                                >

                                    <button
                                        type="button"
                                        class="btn btn-secondary btn-small"
                                        onclick="editContent('${jsEscape(itemId)}')"
                                    >
                                        ✏️ Editar
                                    </button>


                                    ${
                                        category ===
                                        "serie"

                                        ? `

                                            <button
                                                type="button"
                                                class="btn btn-primary btn-small"
                                                onclick="manageEpisodes('${jsEscape(itemId)}')"
                                            >
                                                📺 Episodios
                                            </button>

                                        `

                                        : ""
                                    }


                                    <button
                                        type="button"
                                        class="btn btn-danger btn-small"
                                        onclick="deleteContent('${jsEscape(itemId)}')"
                                    >
                                        🗑️
                                    </button>

                                </div>

                            </td>

                        </tr>

                    `;

                }
            )
            .join("");

}


/* =========================================================
   ACTUALIZAR CONTADORES DEL CATÁLOGO
========================================================= */

function updateCatalogCounter(
    filtered = catalog
) {

    const count =
        filtered.length;


    const possibleIds = [

        "catalogCount",
        "contentCount",
        "moviesCount",
        "catalogTotal",
        "movieCount"

    ];


    possibleIds.forEach(
        id => {

            const element =
                $(id);


            if (!element) return;


            element.textContent =
                count === 1

                    ? "1 contenido"

                    : `${count} contenidos`;

        }
    );

}


/* =========================================================
   BADGE DE CATEGORÍA
========================================================= */

function categoryBadge(
    category
) {

    const label = {

        pelicula:
            "Película",

        serie:
            "Serie",

        terror:
            "Terror"

    }[category] ||
    category;


    return `

        <span
            class="badge badge-${escapeHtml(category)}"
        >
            ${escapeHtml(label)}
        </span>

    `;

}


/* =========================================================
   ABRIR AGREGAR
========================================================= */

function openAddModal() {

    resetContentForm();


    showSection(
        "add",
        document.querySelector(
            '[data-section="add"]'
        )
    );

}


/* =========================================================
   RESET FORMULARIO
========================================================= */

function resetContentForm() {

    const form =
        $("contentForm");


    if (form) {

        form.reset();

    }


    setValue(
        "contentId",
        ""
    );


    setValue(
        "contentCategory",
        "pelicula"
    );


    setValue(
        "contentFeatured",
        "false"
    );

}


/* =========================================================
   GUARDAR CONTENIDO
========================================================= */

async function saveContent(
    event
) {

    if (event) {

        event.preventDefault();

    }


    const item =
        buildContentFromForm();


    if (!item.title) {

        showToast(
            "Debes introducir un título.",
            "error"
        );

        return;

    }


    /*
       Si se seleccionó Terror,
       guardamos category = terror.

       Esto ayuda a que el catálogo público
       también pueda identificarlo directamente.
    */

    if (
        normalizeCategory(
            item.category
        ) === "terror"
    ) {

        item.category =
            "terror";

        item.type =
            "terror";

    }


    try {

        const response =
            await api(
                "/api/catalog",
                {

                    method:
                        "POST",

                    body:
                        JSON.stringify(
                            item
                        )

                }
            );


        const createdItem =
            extractCatalogItem(
                response
            );


        if (createdItem) {

            const createdId =
                getContentId(
                    createdItem
                );


            if (createdId) {

                const existingIndex =
                    catalog.findIndex(
                        element =>
                            getContentId(
                                element
                            ) ===
                            createdId
                    );


                if (
                    existingIndex >= 0
                ) {

                    catalog[
                        existingIndex
                    ] =
                        createdItem;

                }

                else {

                    catalog.push(
                        createdItem
                    );

                }

            }

        }


        showToast(
            "Contenido agregado correctamente.",
            "success"
        );


        resetContentForm();


        await loadCatalog();


        showSection(
            "catalog",
            document.querySelector(
                '[data-section="catalog"]'
            )
        );


    }

    catch (error) {

        console.error(
            "ERROR GUARDANDO CONTENIDO:",
            error
        );


        showToast(
            error.message,
            "error"
        );

    }

}


/* =========================================================
   CONSTRUIR CONTENIDO
========================================================= */

function buildContentFromForm() {

    return {

        title:
            getValue(
                "contentTitle"
            ).trim(),


        category:
            getValue(
                "contentCategory"
            ),


        year:
            getValue(
                "contentYear"
            ).trim(),


        image:
            getValue(
                "contentImage"
            ).trim(),


        video:
            getValue(
                "contentVideo"
            ).trim(),


        description:
            getValue(
                "contentDescription"
            ).trim(),


        genre:
            getValue(
                "contentGenre"
            ).trim(),


        duration:
            getValue(
                "contentDuration"
            ).trim(),


        rating:
            getValue(
                "contentRating"
            ).trim(),


        featured:
            getValue(
                "contentFeatured"
            ) === "true"

    };

}


/* =========================================================
   EDITAR CONTENIDO
========================================================= */

function editContent(
    id
) {

    const item =
        findCatalogItemById(
            id
        );


    if (!item) {

        console.error(
            "EDIT CONTENT: contenido no encontrado",
            {
                requestedId:
                    id,

                catalog
            }
        );


        showToast(
            "Contenido no encontrado.",
            "error"
        );

        return;

    }


    const realId =
        getContentId(
            item
        );


    if (!realId) {

        showToast(
            "El contenido no tiene un identificador válido.",
            "error"
        );

        return;

    }


    setValue(
        "editContentId",
        realId
    );


    setValue(
        "editTitle",
        item.title ||
        item.name ||
        ""
    );


    setValue(
        "editCategory",
        getRealCategory(
            item
        )
    );


    setValue(
        "editYear",
        item.year ||
        ""
    );


    setValue(
        "editImage",
        item.image ||
        item.poster ||
        ""
    );


    setValue(
        "editVideo",
        item.video ||
        item.url ||
        item.videoUrl ||
        ""
    );


    setValue(
        "editDescription",
        item.description ||
        ""
    );


    setValue(
        "editGenre",
        Array.isArray(
            item.genre
        )

            ? item.genre.join(", ")

            : item.genre ||
              getAllGenres(item).join(", ")

    );


    setValue(
        "editDuration",
        item.duration ||
        ""
    );


    setValue(
        "editRating",
        item.rating ||
        ""
    );


    setValue(
        "editFeatured",

        item.featured === true ||
        item.featured === "true"

            ? "true"

            : "false"

    );


    const modal =
        $("contentModal");


    if (modal) {

        modal.classList.add(
            "show"
        );

    }

}


/* =========================================================
   ACTUALIZAR CONTENIDO
========================================================= */

async function updateContent(
    event
) {

    if (event) {

        event.preventDefault();

    }


    const id =
        getValue(
            "editContentId"
        );


    if (!id) {

        showToast(
            "El contenido no tiene un ID válido.",
            "error"
        );

        return;

    }


    const original =
        findCatalogItemById(
            id
        );


    if (!original) {

        showToast(
            "No se encontró el contenido original.",
            "error"
        );

        return;

    }


    const updated = {

        ...original,


        title:
            getValue(
                "editTitle"
            ).trim(),


        category:
            getValue(
                "editCategory"
            ),


        year:
            getValue(
                "editYear"
            ).trim(),


        image:
            getValue(
                "editImage"
            ).trim(),


        video:
            getValue(
                "editVideo"
            ).trim(),


        description:
            getValue(
                "editDescription"
            ).trim(),


        genre:
            getValue(
                "editGenre"
            ).trim(),


        duration:
            getValue(
                "editDuration"
            ).trim(),


        rating:
            getValue(
                "editRating"
            ).trim(),


        featured:
            getValue(
                "editFeatured"
            ) === "true"

    };


    /*
       Terror explícito
    */

    if (
        normalizeCategory(
            updated.category
        ) === "terror"
    ) {

        updated.category =
            "terror";

        updated.type =
            "terror";

    }


    try {

        const response =
            await api(

                "/api/catalog/" +
                encodeURIComponent(
                    id
                ),

                {

                    method:
                        "PUT",

                    body:
                        JSON.stringify(
                            updated
                        )

                }

            );


        const serverItem =
            extractCatalogItem(
                response
            );


        if (serverItem) {

            const serverId =
                getContentId(
                    serverItem
                );


            if (serverId) {

                const index =
                    catalog.findIndex(
                        item =>
                            getContentId(
                                item
                            ) ===
                            serverId
                    );


                if (
                    index >= 0
                ) {

                    catalog[index] =
                        serverItem;

                }

            }

        }


        closeModal(
            "contentModal"
        );


        showToast(
            "Contenido actualizado.",
            "success"
        );


        await loadCatalog();


    }

    catch (error) {

        console.error(
            "ERROR ACTUALIZANDO CONTENIDO:",
            error
        );


        showToast(
            error.message,
            "error"
        );

    }

}


/* =========================================================
   SERIES — CARGAR
========================================================= */

function loadEpisodesSeries() {

    episodesSeries =
        catalog.filter(
            item =>
                getRealCategory(
                    item
                ) ===
                "serie"
        );


    renderEpisodesSeries();

}


/* =========================================================
   SERIES — RENDER
========================================================= */

function renderEpisodesSeries() {

    const container =
        $("episodesSeriesContainer");


    if (!container) return;


    const search =
        getValue(
            "episodesSearch"
        )
        .trim()
        .toLowerCase();


    const filtered =
        episodesSeries.filter(
            series => {

                const title =
                    String(
                        series.title ||
                        series.name ||
                        ""
                    ).toLowerCase();


                const id =
                    getContentId(
                        series
                    ).toLowerCase();


                return (

                    !search ||

                    title.includes(
                        search
                    ) ||

                    id.includes(
                        search
                    )

                );

            }
        );


    updateSeriesCounter(
        filtered
    );


    if (!filtered.length) {

        container.innerHTML = `

            <div class="empty">

                ${
                    episodesSeries.length

                        ? "No se encontraron series."

                        : "Todavía no tienes ninguna serie en el catálogo."

                }

            </div>

        `;

        return;

    }


    container.innerHTML =
        filtered
            .map(
                series => {

                    const seriesId =
                        getContentId(
                            series
                        );


                    const id =
                        jsEscape(
                            seriesId
                        );


                    const title =
                        escapeHtml(
                            series.title ||
                            series.name ||
                            "Serie sin título"
                        );


                    const image =
                        series.image ||
                        series.poster ||
                        "";


                    const seasons =
                        Array.isArray(
                            series.seasons
                        )

                            ? series.seasons

                            : [];


                    const episodeCount =
                        seasons.reduce(

                            (
                                total,
                                season
                            ) => {

                                return (

                                    total +

                                    (

                                        Array.isArray(
                                            season.episodes
                                        )

                                            ? season.episodes.length

                                            : 0

                                    )

                                );

                            },

                            0

                        );


                    return `

                        <div
                            class="panel"
                            style="
                                margin-bottom:15px;
                                display:flex;
                                align-items:center;
                                justify-content:space-between;
                                gap:20px;
                                flex-wrap:wrap;
                            "
                        >

                            <div
                                style="
                                    display:flex;
                                    align-items:center;
                                    gap:15px;
                                    min-width:0;
                                "
                            >

                                ${
                                    image

                                        ? `

                                            <img
                                                src="${escapeHtml(image)}"
                                                alt="${title}"
                                                style="
                                                    width:70px;
                                                    height:95px;
                                                    object-fit:cover;
                                                    border-radius:8px;
                                                    background:#181818;
                                                    flex-shrink:0;
                                                "
                                                onerror="
                                                    this.style.display='none'
                                                "
                                            >

                                        `

                                        : `

                                            <div
                                                style="
                                                    width:70px;
                                                    height:95px;
                                                    border-radius:8px;
                                                    background:#181818;
                                                    display:flex;
                                                    align-items:center;
                                                    justify-content:center;
                                                    font-size:28px;
                                                    flex-shrink:0;
                                                "
                                            >
                                                📺
                                            </div>

                                        `
                                }


                                <div
                                    style="
                                        min-width:0;
                                    "
                                >

                                    <h3
                                        style="
                                            margin-bottom:7px;
                                        "
                                    >
                                        ${title}
                                    </h3>


                                    <div
                                        style="
                                            color:#999;
                                            font-size:13px;
                                        "
                                    >

                                        ${seasons.length}
                                        temporada(s)

                                        ·

                                        ${episodeCount}
                                        episodio(s)

                                    </div>


                                    <code
                                        style="
                                            display:block;
                                            margin-top:7px;
                                            color:#777;
                                            font-size:12px;
                                        "
                                    >
                                        ${escapeHtml(seriesId)}
                                    </code>

                                </div>

                            </div>


                            <button
                                type="button"
                                class="btn btn-primary"
                                onclick="manageEpisodes('${id}')"
                            >
                                📺 Administrar episodios
                            </button>

                        </div>

                    `;

                }
            )
            .join("");

}


/* =========================================================
   CONTADOR SERIES
========================================================= */

function updateSeriesCounter(
    filtered
) {

    const count =
        filtered.length;


    const possibleIds = [

        "seriesCount",
        "episodesSeriesCount",
        "seriesTotal",
        "contentSeriesCount"

    ];


    possibleIds.forEach(
        id => {

            const element =
                $(id);


            if (!element) return;


            element.textContent =
                count === 1

                    ? "1 serie"

                    : `${count} series`;

        }
    );

}


/* =========================================================
   ADMINISTRAR EPISODIOS
========================================================= */

function manageEpisodes(
    id
) {

    const series =
        findCatalogItemById(
            id
        );


    if (!series) {

        showToast(
            "Serie no encontrada.",
            "error"
        );

        return;

    }


    if (
        getRealCategory(
            series
        ) !==
        "serie"
    ) {

        showToast(
            "Este contenido no es una serie.",
            "error"
        );

        return;

    }


    const realId =
        getContentId(
            series
        );


    if (!realId) {

        showToast(
            "Esta serie no tiene un identificador válido.",
            "error"
        );

        return;

    }


    editingSeriesId =
        realId;


    editingSeries =
        series;


    editingSeasons =

        Array.isArray(
            series.seasons
        )

            ? JSON.parse(
                JSON.stringify(
                    series.seasons
                )
            )

            : [];


    setText(
        "episodesSeriesTitle",
        series.title ||
        series.name ||
        "Serie"
    );


    renderSeasons();


    const modal =
        $("episodesModal");


    if (modal) {

        modal.classList.add(
            "show"
        );

    }

}


/* =========================================================
   RENDER TEMPORADAS
========================================================= */

function renderSeasons() {

    const container =
        $("seasonsContainer");


    if (!container) return;


    if (
        !editingSeasons.length
    ) {

        container.innerHTML = `

            <div class="empty">

                Esta serie todavía no tiene temporadas.

                <br><br>

                Presiona
                <strong>
                    "Nueva temporada"
                </strong>
                para comenzar.

            </div>

        `;

        return;

    }


    container.innerHTML =
        editingSeasons
            .map(
                (
                    season,
                    seasonIndex
                ) => {

                    const number =
                        Number(
                            season.number
                        ) ||
                        seasonIndex + 1;


                    const episodes =
                        Array.isArray(
                            season.episodes
                        )

                            ? season.episodes

                            : [];


                    return `

                        <div
                            class="panel"
                            style="
                                margin-bottom:20px;
                                border:1px solid #282828;
                            "
                        >

                            <div
                                style="
                                    display:flex;
                                    justify-content:space-between;
                                    align-items:center;
                                    gap:15px;
                                    margin-bottom:18px;
                                    flex-wrap:wrap;
                                "
                            >

                                <div>

                                    <h3>
                                        Temporada ${number}
                                    </h3>

                                    <span
                                        style="
                                            color:#999;
                                            font-size:13px;
                                        "
                                    >

                                        ${episodes.length}
                                        episodio(s)

                                    </span>

                                </div>


                                <div
                                    style="
                                        display:flex;
                                        gap:8px;
                                        flex-wrap:wrap;
                                    "
                                >

                                    <button
                                        type="button"
                                        class="btn btn-primary btn-small"
                                        onclick="addEpisode(${seasonIndex})"
                                    >
                                        ➕ Episodio
                                    </button>


                                    <button
                                        type="button"
                                        class="btn btn-danger btn-small"
                                        onclick="removeSeason(${seasonIndex})"
                                    >
                                        🗑️ Temporada
                                    </button>

                                </div>

                            </div>


                            <div>

                                ${
                                    episodes.length

                                    ?

                                    episodes
                                        .map(
                                            (
                                                episode,
                                                episodeIndex
                                            ) => {

                                                const episodeNumber =
                                                    Number(
                                                        episode.number
                                                    ) ||
                                                    episodeIndex + 1;


                                                const episodeTitle =
                                                    escapeHtml(
                                                        episode.title ||
                                                        `Episodio ${episodeNumber}`
                                                    );


                                                const episodeVideo =
                                                    escapeHtml(
                                                        episode.video ||
                                                        episode.url ||
                                                        episode.videoUrl ||
                                                        ""
                                                    );


                                                const episodeImage =
                                                    escapeHtml(
                                                        episode.image ||
                                                        episode.thumbnail ||
                                                        ""
                                                    );


                                                return `

                                                    <div
                                                        style="
                                                            display:grid;
                                                            grid-template-columns:
                                                                70px
                                                                minmax(160px,1fr)
                                                                minmax(220px,1.5fr)
                                                                minmax(180px,1fr)
                                                                auto;
                                                            gap:10px;
                                                            align-items:end;
                                                            margin-bottom:14px;
                                                            padding:14px;
                                                            background:#0d0d0d;
                                                            border:1px solid #242424;
                                                            border-radius:10px;
                                                        "
                                                    >

                                                        <div class="form-group">

                                                            <label>
                                                                Episodio
                                                            </label>

                                                            <input
                                                                type="number"
                                                                min="1"
                                                                value="${episodeNumber}"
                                                                onchange="
                                                                    updateEpisode(
                                                                        ${seasonIndex},
                                                                        ${episodeIndex},
                                                                        'number',
                                                                        this.value
                                                                    )
                                                                "
                                                            >

                                                        </div>


                                                        <div class="form-group">

                                                            <label>
                                                                Título
                                                            </label>

                                                            <input
                                                                value="${episodeTitle}"
                                                                placeholder="Episodio 1"
                                                                onchange="
                                                                    updateEpisode(
                                                                        ${seasonIndex},
                                                                        ${episodeIndex},
                                                                        'title',
                                                                        this.value
                                                                    )
                                                                "
                                                            >

                                                        </div>


                                                        <div class="form-group">

                                                            <label>
                                                                URL del video
                                                            </label>

                                                            <input
                                                                value="${episodeVideo}"
                                                                placeholder="https://..."
                                                                onchange="
                                                                    updateEpisode(
                                                                        ${seasonIndex},
                                                                        ${episodeIndex},
                                                                        'video',
                                                                        this.value
                                                                    )
                                                                "
                                                            >

                                                        </div>


                                                        <div class="form-group">

                                                            <label>
                                                                Imagen / Thumbnail
                                                            </label>

                                                            <input
                                                                value="${episodeImage}"
                                                                placeholder="images/episodio1.jpg"
                                                                onchange="
                                                                    updateEpisode(
                                                                        ${seasonIndex},
                                                                        ${episodeIndex},
                                                                        'image',
                                                                        this.value
                                                                    )
                                                                "
                                                            >

                                                        </div>


                                                        <button
                                                            type="button"
                                                            class="btn btn-danger btn-small"
                                                            onclick="
                                                                removeEpisode(
                                                                    ${seasonIndex},
                                                                    ${episodeIndex}
                                                                )
                                                            "
                                                            title="Eliminar episodio"
                                                        >
                                                            ❌
                                                        </button>

                                                    </div>

                                                `;

                                            }
                                        )
                                        .join("")

                                    :

                                    `

                                        <div
                                            class="empty"
                                            style="padding:20px;"
                                        >

                                            Esta temporada no tiene episodios.

                                        </div>

                                    `

                                }

                            </div>

                        </div>

                    `;

                }
            )
            .join("");

}


/* =========================================================
   AGREGAR TEMPORADA
========================================================= */

function addSeason() {

    const nextNumber =

        editingSeasons.length

            ?

            Math.max(

                ...editingSeasons.map(
                    season =>
                        Number(
                            season.number
                        ) || 0
                )

            ) + 1

            :

            1;


    editingSeasons.push({

        number:
            nextNumber,

        episodes:
            []

    });


    renderSeasons();

}


/* =========================================================
   ELIMINAR TEMPORADA
========================================================= */

function removeSeason(
    index
) {

    const season =
        editingSeasons[
            index
        ];


    if (!season) return;


    const number =
        season.number ||
        index + 1;


    if (
        !confirm(
            `¿Eliminar la Temporada ${number} y todos sus episodios?`
        )
    ) {

        return;

    }


    editingSeasons.splice(
        index,
        1
    );


    renderSeasons();

}


/* =========================================================
   AGREGAR EPISODIO
========================================================= */

function addEpisode(
    seasonIndex
) {

    const season =
        editingSeasons[
            seasonIndex
        ];


    if (!season) return;


    if (
        !Array.isArray(
            season.episodes
        )
    ) {

        season.episodes = [];

    }


    const nextNumber =

        season.episodes.length

            ?

            Math.max(

                ...season.episodes.map(
                    episode =>
                        Number(
                            episode.number
                        ) || 0
                )

            ) + 1

            :

            1;


    season.episodes.push({

        number:
            nextNumber,

        title:
            `Episodio ${nextNumber}`,

        video:
            "",

        image:
            ""

    });


    renderSeasons();

}


/* =========================================================
   ACTUALIZAR EPISODIO
========================================================= */

function updateEpisode(
    seasonIndex,
    episodeIndex,
    field,
    value
) {

    const season =
        editingSeasons[
            seasonIndex
        ];


    if (!season) return;


    if (
        !Array.isArray(
            season.episodes
        )
    ) {

        season.episodes = [];

    }


    const episode =
        season.episodes[
            episodeIndex
        ];


    if (!episode) return;


    if (
        field === "number"
    ) {

        episode.number =
            Number(value) ||
            episodeIndex + 1;

    }

    else {

        episode[field] =
            String(
                value || ""
            ).trim();

    }

}


/* =========================================================
   ELIMINAR EPISODIO
========================================================= */

function removeEpisode(
    seasonIndex,
    episodeIndex
) {

    const season =
        editingSeasons[
            seasonIndex
        ];


    if (!season) return;


    const episode =
        season.episodes[
            episodeIndex
        ];


    if (!episode) return;


    if (
        !confirm(
            `¿Eliminar "${episode.title || "este episodio"}"?`
        )
    ) {

        return;

    }


    season.episodes.splice(
        episodeIndex,
        1
    );


    renderSeasons();

}


/* =========================================================
   GUARDAR TEMPORADAS / EPISODIOS
========================================================= */

async function saveEpisodes() {

    if (!editingSeriesId) {

        showToast(
            "No hay ninguna serie seleccionada.",
            "error"
        );

        return;

    }


    for (
        let s = 0;
        s < editingSeasons.length;
        s++
    ) {

        const season =
            editingSeasons[s];


        if (
            !Array.isArray(
                season.episodes
            )
        ) {

            continue;

        }


        for (
            let e = 0;
            e < season.episodes.length;
            e++
        ) {

            const episode =
                season.episodes[e];


            if (

                !episode.video ||

                !String(
                    episode.video
                ).trim()

            ) {

                showToast(
                    `La Temporada ${season.number} — Episodio ${episode.number || e + 1} no tiene URL de video.`,
                    "error"
                );

                return;

            }

        }

    }


    try {

        const updated = {

            ...editingSeries,

            seasons:
                JSON.parse(
                    JSON.stringify(
                        editingSeasons
                    )
                )

        };


        const response =
            await api(

                "/api/catalog/" +
                encodeURIComponent(
                    editingSeriesId
                ),

                {

                    method:
                        "PUT",

                    body:
                        JSON.stringify(
                            updated
                        )

                }

            );


        const serverItem =
            extractCatalogItem(
                response
            );


        if (serverItem) {

            const serverId =
                getContentId(
                    serverItem
                );


            if (serverId) {

                const index =
                    catalog.findIndex(
                        item =>
                            getContentId(
                                item
                            ) ===
                            serverId
                    );


                if (
                    index >= 0
                ) {

                    catalog[index] =
                        serverItem;

                }

            }

        }


        showToast(
            "Temporadas y episodios guardados correctamente.",
            "success"
        );


        closeModal(
            "episodesModal"
        );


        await loadCatalog();


        editingSeriesId =
            null;

        editingSeries =
            null;

        editingSeasons =
            [];


    }

    catch (error) {

        console.error(
            "ERROR GUARDANDO EPISODIOS:",
            error
        );


        showToast(
            error.message,
            "error"
        );

    }

}


/* =========================================================
   ELIMINAR CONTENIDO
========================================================= */

async function deleteContent(
    id
) {

    const item =
        findCatalogItemById(
            id
        );


    const title =
        item?.title ||
        item?.name ||
        id;


    if (
        !confirm(
            `¿Enviar "${title}" a la papelera?`
        )
    ) {

        return;

    }


    try {

        const realId =
            getContentId(
                item
            ) ||
            id;


        await api(

            "/api/catalog/" +
            encodeURIComponent(
                realId
            ),

            {

                method:
                    "DELETE",

                body:
                    JSON.stringify({})

            }

        );


        showToast(
            "Contenido enviado a la papelera.",
            "success"
        );


        await loadCatalog();

        await loadTrash();


    }

    catch (error) {

        console.error(
            "ERROR ELIMINANDO CONTENIDO:",
            error
        );


        showToast(
            error.message,
            "error"
        );

    }

}


/* =========================================================
   PAPELERA — CARGAR
========================================================= */

async function loadTrash() {

    try {

        const response =
            await api(
                "/api/trash"
            );


        trash =
            extractCatalogArray(
                response
            );


        renderTrash();

        renderDashboard();


    }

    catch (error) {

        console.error(
            "ERROR CARGANDO PAPELERA:",
            error
        );


        showToast(
            error.message,
            "error"
        );

    }

}


/* =========================================================
   RENDER PAPELERA
========================================================= */

function renderTrash() {

    const table =
        $("trashTable");


    if (!table) return;


    if (!trash.length) {

        table.innerHTML = `

            <tr>

                <td colspan="4">

                    <div class="empty">

                        La papelera está vacía.

                    </div>

                </td>

            </tr>

        `;

        return;

    }


    table.innerHTML =
        trash
            .map(
                item => {

                    const itemId =
                        getContentId(
                            item
                        );


                    const id =
                        escapeHtml(
                            itemId
                        );


                    const title =
                        escapeHtml(
                            item.title ||
                            item.name ||
                            "Sin título"
                        );


                    const category =
                        getRealCategory(
                            item
                        );


                    return `

                        <tr>

                            <td>

                                <strong>
                                    ${title}
                                </strong>

                            </td>


                            <td>

                                ${categoryBadge(
                                    category
                                )}

                            </td>


                            <td>

                                <code>
                                    ${id}
                                </code>

                            </td>


                            <td>

                                <div class="actions">

                                    <button
                                        type="button"
                                        class="btn btn-success btn-small"
                                        onclick="restoreContent('${jsEscape(itemId)}')"
                                    >
                                        ♻️ Restaurar
                                    </button>


                                    <button
                                        type="button"
                                        class="btn btn-danger btn-small"
                                        onclick="permanentDelete('${jsEscape(itemId)}')"
                                    >
                                        ❌ Eliminar
                                    </button>

                                </div>

                            </td>

                        </tr>

                    `;

                }
            )
            .join("");

}


/* =========================================================
   RESTAURAR
========================================================= */

async function restoreContent(
    id
) {

    const item =
        trash.find(
            element =>
                getContentId(
                    element
                ) ===
                String(id)
        );


    const title =
        item?.title ||
        item?.name ||
        id;


    if (
        !confirm(
            `¿Restaurar "${title}"?`
        )
    ) {

        return;

    }


    try {

        await api(

            "/api/trash/" +
            encodeURIComponent(
                id
            ) +
            "/restore",

            {

                method:
                    "POST",

                body:
                    JSON.stringify({})

            }

        );


        showToast(
            "Contenido restaurado.",
            "success"
        );


        await loadCatalog();

        await loadTrash();


    }

    catch (error) {

        showToast(
            error.message,
            "error"
        );

    }

}


/* =========================================================
   ELIMINACIÓN PERMANENTE
========================================================= */

async function permanentDelete(
    id
) {

    const item =
        trash.find(
            element =>
                getContentId(
                    element
                ) ===
                String(id)
        );


    const title =
        item?.title ||
        item?.name ||
        id;


    if (
        !confirm(
            `⚠️ ¿Eliminar DEFINITIVAMENTE "${title}"?\n\nEsta acción no se puede deshacer.`
        )
    ) {

        return;

    }


    try {

        await api(

            "/api/trash/" +
            encodeURIComponent(
                id
            ),

            {

                method:
                    "DELETE",

                body:
                    JSON.stringify({})

            }

        );


        showToast(
            "Contenido eliminado definitivamente.",
            "success"
        );


        await loadTrash();


    }

    catch (error) {

        showToast(
            error.message,
            "error"
        );

    }

}


/* =========================================================
   USUARIOS — CARGAR
========================================================= */

async function loadUsers() {

    try {

        const response =
            await api(
                "/api/users"
            );


        users =
            extractUsersArray(
                response
            );


        renderUsers();

        updateStats();

        renderDashboard();


    }

    catch (error) {

        console.error(
            "ERROR CARGANDO USUARIOS:",
            error
        );


        showToast(
            error.message,
            "error"
        );

    }

}


/* =========================================================
   EXTRAER USUARIOS
========================================================= */

function extractUsersArray(
    response
) {

    if (
        Array.isArray(response)
    ) {

        return response;

    }


    if (
        Array.isArray(
            response?.data
        )
    ) {

        return response.data;

    }


    if (
        Array.isArray(
            response?.users
        )
    ) {

        return response.users;

    }


    if (
        Array.isArray(
            response?.items
        )
    ) {

        return response.items;

    }


    return [];

}


/* =========================================================
   RENDER USUARIOS
========================================================= */

function renderUsers() {

    const table =
        $("usersTable");


    if (!table) return;


    const search =
        getValue(
            "userSearch"
        )
        .trim()
        .toLowerCase();


    const filtered =
        users.filter(
            user => {

                const username =
                    String(
                        user.username ||
                        ""
                    ).toLowerCase();


                const email =
                    String(
                        user.email ||
                        ""
                    ).toLowerCase();


                return (

                    !search ||

                    username.includes(
                        search
                    ) ||

                    email.includes(
                        search
                    )

                );

            }
        );


    if (!filtered.length) {

        table.innerHTML = `

            <tr>

                <td colspan="4">

                    <div class="empty">

                        No hay usuarios.

                    </div>

                </td>

            </tr>

        `;

        return;

    }


    table.innerHTML =
        filtered
            .map(
                user => {

                    const id =
                        jsEscape(
                            user.id
                        );


                    const username =
                        escapeHtml(
                            user.username ||
                            "Sin usuario"
                        );


                    const email =
                        escapeHtml(
                            user.email ||
                            ""
                        );


                    const connected =
                        user.connected === true;


                    return `

                        <tr>

                            <td>

                                <strong>
                                    ${username}
                                </strong>

                            </td>


                            <td>

                                ${email}

                            </td>


                            <td>

                                ${
                                    connected

                                    ?

                                    `

                                        <span
                                            class="badge badge-online"
                                        >
                                            ● Conectado
                                        </span>

                                    `

                                    :

                                    `

                                        <span
                                            class="badge badge-offline"
                                        >
                                            ● Desconectado
                                        </span>

                                    `
                                }

                            </td>


                            <td>

                                <div class="actions">

                                    <button
                                        type="button"
                                        class="btn btn-secondary btn-small"
                                        onclick="editUser('${id}')"
                                    >
                                        ✏️
                                    </button>


                                    ${
                                        connected

                                        ?

                                        `

                                            <button
                                                type="button"
                                                class="btn btn-warning btn-small"
                                                onclick="disconnectUser('${id}')"
                                            >
                                                🔌
                                            </button>

                                        `

                                        :

                                        ""
                                    }


                                    <button
                                        type="button"
                                        class="btn btn-danger btn-small"
                                        onclick="deleteUser('${id}')"
                                    >
                                        🗑️
                                    </button>

                                </div>

                            </td>

                        </tr>

                    `;

                }
            )
            .join("");

}


/* =========================================================
   EDITAR USUARIO
========================================================= */

async function editUser(
    id
) {

    const user =
        users.find(
            element =>
                String(
                    element.id
                ) ===
                String(id)
        );


    if (!user) {

        showToast(
            "Usuario no encontrado.",
            "error"
        );

        return;

    }


    setValue(
        "editUserId",
        user.id
    );


    setValue(
        "editUsername",
        user.username ||
        ""
    );


    setValue(
        "editEmail",
        user.email ||
        ""
    );


    setValue(
        "editPassword",
        ""
    );


    setValue(
        "editRole",
        user.role ||
        "user"
    );


    const modal =
        $("userModal");


    if (modal) {

        modal.classList.add(
            "show"
        );

    }

}


/* =========================================================
   ACTUALIZAR USUARIO
========================================================= */

async function updateUser(
    event
) {

    if (event) {

        event.preventDefault();

    }


    const id =
        getValue(
            "editUserId"
        );


    const data = {

        username:
            getValue(
                "editUsername"
            ).trim(),


        email:
            getValue(
                "editEmail"
            ).trim(),


        role:
            getValue(
                "editRole"
            )

    };


    const password =
        getValue(
            "editPassword"
        );


    if (password) {

        data.password =
            password;

    }


    try {

        await api(

            "/api/users/" +
            encodeURIComponent(
                id
            ),

            {

                method:
                    "PUT",

                body:
                    JSON.stringify(
                        data
                    )

            }

        );


        closeModal(
            "userModal"
        );


        showToast(
            "Usuario actualizado.",
            "success"
        );


        await loadUsers();


    }

    catch (error) {

        showToast(
            error.message,
            "error"
        );

    }

}


/* =========================================================
   DESCONECTAR USUARIO
========================================================= */

async function disconnectUser(
    id
) {

    const user =
        users.find(
            element =>
                String(
                    element.id
                ) ===
                String(id)
        );


    if (!user) return;


    if (
        !confirm(
            `¿Desconectar a ${user.username}?`
        )
    ) {

        return;

    }


    try {

        await api(

            "/api/users/" +
            encodeURIComponent(
                id
            ) +
            "/disconnect",

            {

                method:
                    "POST",

                body:
                    JSON.stringify({})

            }

        );


        showToast(
            "Usuario desconectado.",
            "success"
        );


        await loadUsers();


    }

    catch (error) {

        showToast(
            error.message,
            "error"
        );

    }

}


/* =========================================================
   ELIMINAR USUARIO
========================================================= */

async function deleteUser(
    id
) {

    const user =
        users.find(
            element =>
                String(
                    element.id
                ) ===
                String(id)
        );


    if (!user) return;


    if (
        !confirm(
            `⚠️ ¿Eliminar la cuenta de ${user.username}?\n\nTambién se cerrarán sus sesiones.`
        )
    ) {

        return;

    }


    try {

        await api(

            "/api/users/" +
            encodeURIComponent(
                id
            ),

            {

                method:
                    "DELETE",

                body:
                    JSON.stringify({})

            }

        );


        showToast(
            "Usuario eliminado.",
            "success"
        );


        await loadUsers();


    }

    catch (error) {

        showToast(
            error.message,
            "error"
        );

    }

}


/* =========================================================
   ESTADÍSTICAS
========================================================= */

function updateStats() {

    let movies = 0;

    let series = 0;

    let horror = 0;


    catalog.forEach(
        item => {

            const category =
                getRealCategory(
                    item
                );


            if (
                category === "terror"
            ) {

                horror++;

            }

            else if (
                category === "serie"
            ) {

                series++;

            }

            else {

                /*
                   Todo lo que no sea serie ni terror
                   se considera película.

                   Esto evita perder películas si el backend
                   utiliza "movie", "film", "peliculas", etc.
                */

                movies++;

            }

        }
    );


    setText(
        "statMovies",
        movies
    );


    setText(
        "statSeries",
        series
    );


    setText(
        "statHorror",
        horror
    );


    setText(
        "statUsers",
        users.length
    );


    /*
       Otros posibles IDs del dashboard
    */

    setText(
        "dashboardMovies",
        movies
    );


    setText(
        "dashboardSeries",
        series
    );


    setText(
        "dashboardHorror",
        horror
    );


    setText(
        "dashboardUsers",
        users.length
    );


    /*
       DEBUG
    */

    console.log(
        "======================================"
    );

    console.log(
        "📊 ESTADÍSTICAS CINEMAX"
    );

    console.log(
        "🎬 Películas:",
        movies
    );

    console.log(
        "📺 Series:",
        series
    );

    console.log(
        "👻 Terror:",
        horror
    );

    console.log(
        "👤 Usuarios:",
        users.length
    );

    console.log(
        "📦 Total:",
        catalog.length
    );

    console.log(
        "======================================"
    );

}


/* =========================================================
   DASHBOARD
========================================================= */

function renderDashboard() {

    const container =
        $("dashboardRecent");


    if (!container) return;


    const total =
        catalog.length;


    const trashCount =
        trash.length;


    const connected =
        users.filter(
            user =>
                user.connected === true
        ).length;


    container.innerHTML = `

        <div
            style="
                display:grid;
                grid-template-columns:
                    repeat(auto-fit,minmax(180px,1fr));
                gap:12px;
            "
        >

            <div class="panel">

                <div class="stat-label">
                    Contenido total
                </div>

                <strong
                    style="font-size:22px;"
                >
                    ${total}
                </strong>

            </div>


            <div class="panel">

                <div class="stat-label">
                    En papelera
                </div>

                <strong
                    style="font-size:22px;"
                >
                    ${trashCount}
                </strong>

            </div>


            <div class="panel">

                <div class="stat-label">
                    Usuarios conectados
                </div>

                <strong
                    style="font-size:22px;"
                >
                    ${connected}
                </strong>

            </div>

        </div>

    `;

}


/* =========================================================
   MODALES
========================================================= */

function closeModal(
    id
) {

    const modal =
        $(id);


    if (modal) {

        modal.classList.remove(
            "show"
        );

    }

}


/* =========================================================
   CERRAR MODAL FUERA
========================================================= */

function initializeModals() {

    document
        .querySelectorAll(
            ".modal"
        )
        .forEach(
            modal => {

                if (
                    modal.dataset.initialized ===
                    "true"
                ) {

                    return;

                }


                modal.dataset.initialized =
                    "true";


                modal.addEventListener(
                    "click",
                    function(event) {

                        if (
                            event.target ===
                            modal
                        ) {

                            modal.classList.remove(
                                "show"
                            );

                        }

                    }
                );

            }
        );

}


document.addEventListener(
    "DOMContentLoaded",
    initializeModals
);


/* =========================================================
   TOAST
========================================================= */

let toastTimer = null;


function showToast(
    message,
    type = "success"
) {

    const toast =
        $("toast");


    if (!toast) {

        console.log(
            `[${type}]`,
            message
        );

        return;

    }


    toast.textContent =
        message;


    toast.className =
        type;


    toast.style.display =
        "block";


    clearTimeout(
        toastTimer
    );


    toastTimer =
        setTimeout(
            () => {

                toast.style.display =
                    "none";

            },
            3500
        );

}


/* =========================================================
   ESCAPAR HTML
========================================================= */

function escapeHtml(
    value
) {

    return String(
        value ?? ""
    )

    .replace(
        /&/g,
        "&amp;"
    )

    .replace(
        /</g,
        "&lt;"
    )

    .replace(
        />/g,
        "&gt;"
    )

    .replace(
        /"/g,
        "&quot;"
    )

    .replace(
        /'/g,
        "&#039;"
    );

}


/* =========================================================
   ESCAPAR JAVASCRIPT
========================================================= */

function jsEscape(
    value
) {

    return String(
        value ?? ""
    )

    .replace(
        /\\/g,
        "\\\\"
    )

    .replace(
        /'/g,
        "\\'"
    )

    .replace(
        /"/g,
        '\\"'
    )

    .replace(
        /\n/g,
        "\\n"
    )

    .replace(
        /\r/g,
        "\\r"
    );

}


/* =========================================================
   ESCAPE MODALES
========================================================= */

document.addEventListener(
    "keydown",
    function(event) {

        if (
            event.key ===
            "Escape"
        ) {

            document
                .querySelectorAll(
                    ".modal.show"
                )
                .forEach(
                    modal =>
                        modal.classList.remove(
                            "show"
                        )
                );

        }

    }
);


/* =========================================================
   BÚSQUEDA CATÁLOGO
========================================================= */

function initializeCatalogSearch() {

    const search =
        $("catalogSearch");


    if (search) {

        search.addEventListener(
            "input",
            renderCatalog
        );

    }


    const filter =
        $("catalogFilter");


    if (filter) {

        filter.addEventListener(
            "change",
            renderCatalog
        );

    }

}


document.addEventListener(
    "DOMContentLoaded",
    initializeCatalogSearch
);


/* =========================================================
   BÚSQUEDA SERIES
========================================================= */

function initializeEpisodesSearch() {

    const search =
        $("episodesSearch");


    if (search) {

        search.addEventListener(
            "input",
            renderEpisodesSeries
        );

    }

}


document.addEventListener(
    "DOMContentLoaded",
    initializeEpisodesSearch
);


/* =========================================================
   BÚSQUEDA USUARIOS
========================================================= */

function initializeUsersSearch() {

    const search =
        $("userSearch");


    if (search) {

        search.addEventListener(
            "input",
            renderUsers
        );

    }

}


document.addEventListener(
    "DOMContentLoaded",
    initializeUsersSearch
);


/* =========================================================
   COMPROBACIÓN DE SESIÓN
   CADA 5 SEGUNDOS
========================================================= */

setInterval(
    async function() {

        if (!sessionId) {

            return;

        }


        try {

            const response =
                await fetch(

                    API_URL +
                    "/api/users/session/" +
                    encodeURIComponent(
                        sessionId
                    ),

                    {

                        method:
                            "GET",

                        headers: {

                            "Content-Type":
                                "application/json",

                            "X-Session-ID":
                                sessionId,

                            "Authorization":
                                "Bearer " +
                                sessionId

                        }

                    }

                );


            if (
                !response.ok
            ) {

                return;

            }


            const data =
                await response.json();


            if (

                !data.success ||

                !data.active ||

                String(
                    data.user?.role ||
                    "user"
                ).toLowerCase()
                !==
                "admin"

            ) {

                localStorage.removeItem(
                    "cinemax_session_id"
                );


                sessionId = null;

                currentUser = null;


                showLogin(
                    "Tu sesión de administrador ya no está activa."
                );


            }

            else {

                currentUser =
                    data.user;


                setText(
                    "topUsername",
                    currentUser.username ||
                    "Administrador"
                );


                setText(
                    "topEmail",
                    currentUser.email ||
                    ""
                );

            }

        }

        catch (_) {}

    },

    5000
);


/* =========================================================
   ACTUALIZACIÓN AUTOMÁTICA DEL CATÁLOGO
   CADA 30 SEGUNDOS
========================================================= */

setInterval(
    async function() {

        const app =
            $("app");


        if (

            app &&

            app.style.display !==
            "none"

        ) {

            try {

                await loadCatalog();

            }

            catch (_) {}

        }

    },

    30000
);


/* =========================================================
   ACTUALIZACIÓN AUTOMÁTICA DE USUARIOS
   CADA 30 SEGUNDOS
========================================================= */

setInterval(
    async function() {

        const app =
            $("app");


        if (

            app &&

            app.style.display !==
            "none"

        ) {

            try {

                if (
                    $("usersTable")
                ) {

                    await loadUsers();

                }

            }

            catch (_) {}

        }

    },

    30000
);


/* =========================================================
   INICIALIZACIÓN FINAL
========================================================= */

document.addEventListener(
    "DOMContentLoaded",
    function() {

        initializeModals();

        initializeLoginForm();


        if (catalog.length) {

            renderCatalog();

        }


        if (users.length) {

            renderUsers();

        }


        if (trash.length) {

            renderTrash();

        }

    }
);