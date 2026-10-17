/* =====================================================
   GET VIDEO ID FROM URL
===================================================== */

const params = new URLSearchParams(
    window.location.search
);

const videoId = params.get("id");


/* =====================================================
   CHAT HISTORY
===================================================== */

let chatHistory = [];


/* =====================================================
   GET HTML ELEMENTS
===================================================== */

const loading =
    document.getElementById("loading");

const lectureContent =
    document.getElementById("lectureContent");

const lectureNumber =
    document.getElementById("lectureNumber");

const lectureTitle =
    document.getElementById("lectureTitle");

const lectureMeta =
    document.getElementById("lectureMeta");

const youtubePlayer =
    document.getElementById("youtubePlayer");


/* =====================================================
   NAVIGATION ELEMENTS
===================================================== */

const previousLecture =
    document.getElementById("previousLecture");

const nextLecture =
    document.getElementById("nextLecture");

const completeLecture =
    document.getElementById("completeLecture");

const progressText =
    document.getElementById("progressText");

const progressFill =
    document.getElementById("progressFill");


/* =====================================================
   AI ELEMENTS
===================================================== */

const questionInput =
    document.getElementById("questionInput");

const askAI =
    document.getElementById("askAI");

const aiError =
    document.getElementById("aiError");

const chatHistoryContainer =
    document.getElementById("chatHistory");


/* =====================================================
   COURSE DATA
===================================================== */

let course = null;
let currentLecture = null;
let currentIndex = -1;


/* =====================================================
   CHECK VIDEO ID
===================================================== */

if (!videoId) {

    loading.textContent =
        "No lecture was selected.";

} else {

    loadLecture();

}


/* =====================================================
   LOAD COURSE
===================================================== */

function getCourse() {

    const savedCourse =
        localStorage.getItem(
            "coursemind.course"
        );

    if (!savedCourse) {

        return null;

    }

    try {

        return JSON.parse(savedCourse);

    } catch (error) {

        console.error(
            "Could not read saved course:",
            error
        );

        return null;

    }

}


/* =====================================================
   LOAD LECTURE
===================================================== */

function loadLecture() {

    course = getCourse();


    /* -------------------------------------------------
       CHECK COURSE
    ------------------------------------------------- */

    if (!course || !course.videos) {

        loading.textContent =
            "Course information was not found.";

        return;

    }


    /* -------------------------------------------------
       FIND CURRENT LECTURE
    ------------------------------------------------- */

    currentIndex =
        course.videos.findIndex(
            function(video) {

                return video.video_id === videoId;

            }
        );


    /* -------------------------------------------------
       CHECK LECTURE
    ------------------------------------------------- */

    if (currentIndex === -1) {

        loading.textContent =
            "Lecture not found in the saved course.";

        return;

    }


    currentLecture =
        course.videos[currentIndex];


    console.log(
        "Lecture opened:",
        currentLecture
    );

    console.log(
        "Video ID:",
        videoId
    );


    /* -------------------------------------------------
       DISPLAY LECTURE INFORMATION
    ------------------------------------------------- */

    lectureNumber.textContent =
        `Lecture ${currentIndex + 1}`;

    lectureTitle.textContent =
        currentLecture.title;

    lectureMeta.textContent =
        course.name ||
        course.title ||
        "CourseMind Course";


    /* -------------------------------------------------
       LOAD YOUTUBE VIDEO
    ------------------------------------------------- */

    youtubePlayer.src =
        `https://www.youtube.com/embed/${videoId}`;


    /* -------------------------------------------------
       BROWSER TITLE
    ------------------------------------------------- */

    document.title =
        `CourseMind — ${currentLecture.title}`;


    /* -------------------------------------------------
       UPDATE PROGRESS
    ------------------------------------------------- */

    updateProgress();


    /* -------------------------------------------------
       UPDATE NAVIGATION
    ------------------------------------------------- */

    updateNavigation();


    /* -------------------------------------------------
       UPDATE COMPLETION BUTTON
    ------------------------------------------------- */

    updateCompletionButton();

    /* -------------------------------------------------
    LOAD LECTURE SUMMARY
    ------------------------------------------------- */

    loadLectureSummary();



    /* -------------------------------------------------
       SHOW LECTURE
    ------------------------------------------------- */

    loading.style.display =
        "none";

    lectureContent.style.display =
        "block";

}


/* =====================================================
   UPDATE PROGRESS
===================================================== */

function updateProgress() {

    if (!course || !course.videos) {

        return;

    }


    const total =
        course.videos.length;

    const current =
        currentIndex + 1;


    progressText.textContent =
        `Lecture ${current} of ${total}`;


    const percentage =
        (current / total) * 100;


    progressFill.style.width =
        `${percentage}%`;

}


/* =====================================================
   GET COMPLETED LECTURES
===================================================== */

function getCompletedLectures() {

    const saved =
        localStorage.getItem(
            "coursemind.completedLectures"
        );


    if (!saved) {

        return {};

    }


    try {

        return JSON.parse(saved);

    } catch {

        return {};

    }

}


/* =====================================================
   SAVE COMPLETED LECTURES
===================================================== */

function saveCompletedLectures(data) {

    localStorage.setItem(
        "coursemind.completedLectures",
        JSON.stringify(data)
    );

}


/* =====================================================
   UPDATE COMPLETION BUTTON
===================================================== */

function updateCompletionButton() {

    if (!completeLecture) {

        return;

    }


    const completed =
        getCompletedLectures();


    if (completed[videoId]) {

        completeLecture.textContent =
            "✓ Completed";

        completeLecture.classList.add(
            "completed"
        );

        completeLecture.disabled =
            true;

    } else {

        completeLecture.textContent =
            "✓ Mark as Completed";

        completeLecture.classList.remove(
            "completed"
        );

        completeLecture.disabled =
            false;

    }

}


/* =====================================================
   MARK LECTURE AS COMPLETED
===================================================== */

completeLecture.addEventListener(
    "click",
    function() {

        const completed =
            getCompletedLectures();


        completed[videoId] =
            true;


        saveCompletedLectures(
            completed
        );


        updateCompletionButton();


        console.log(
            "Lecture completed:",
            videoId
        );

    }
);


/* =====================================================
   UPDATE NAVIGATION
===================================================== */

function updateNavigation() {

    if (!course || !course.videos) {

        return;

    }


    /* -------------------------------------------------
       PREVIOUS BUTTON
    ------------------------------------------------- */

    if (currentIndex <= 0) {

        previousLecture.disabled =
            true;

    } else {

        previousLecture.disabled =
            false;

    }


    /* -------------------------------------------------
       NEXT BUTTON
    ------------------------------------------------- */

    if (
        currentIndex >=
        course.videos.length - 1
    ) {

        nextLecture.disabled =
            true;

    } else {

        nextLecture.disabled =
            false;

    }

}


/* =====================================================
   PREVIOUS LECTURE
===================================================== */

previousLecture.addEventListener(
    "click",
    function() {

        if (currentIndex <= 0) {

            return;

        }


        const previous =
            course.videos[
                currentIndex - 1
            ];


        window.location.href =
            `lecture.html?id=${previous.video_id}`;

    }
);


/* =====================================================
   NEXT LECTURE
===================================================== */

nextLecture.addEventListener(
    "click",
    function() {

        if (
            currentIndex >=
            course.videos.length - 1
        ) {

            return;

        }


        const next =
            course.videos[
                currentIndex + 1
            ];


        window.location.href =
            `lecture.html?id=${next.video_id}`;

    }
);


/* =====================================================
   ASK AI BUTTON
===================================================== */

askAI.addEventListener(
    "click",
    askCourseMind
);

/* Suggested prompts in the lecture AI chat */
document.querySelectorAll("[data-lecture-q]").forEach(function(button) {
    button.addEventListener("click", function() {
        questionInput.value = button.dataset.lectureQ || "";
        questionInput.focus();
        askCourseMind();
    });
});


/* =====================================================
   PRESS ENTER TO ASK
===================================================== */

questionInput.addEventListener(
    "keydown",
    function(event) {

        if (event.key === "Enter") {

            askCourseMind();

        }

    }
);


/* =====================================================
   ASK COURSE MIND
===================================================== */

async function askCourseMind() {

    /* -------------------------------------------------
       GET QUESTION
    ------------------------------------------------- */

    const question =
        questionInput.value.trim();


    /* -------------------------------------------------
       DON'T SEND EMPTY QUESTION
    ------------------------------------------------- */

    if (!question) {

        questionInput.focus();

        return;

    }


    /* -------------------------------------------------
       LOADING STATE
    ------------------------------------------------- */

    askAI.disabled = true;
    askAI.textContent = "Thinking...";
    aiError.style.display = "none";

    const pendingMessage = document.createElement("div");
    pendingMessage.className = "chat-message pending-message";

    const pendingQuestion = document.createElement("div");
    pendingQuestion.className = "ai-question";
    const pendingLabel = document.createElement("strong");
    pendingLabel.textContent = "You:";
    const pendingText = document.createElement("span");
    pendingText.textContent = ` ${question}`;
    pendingQuestion.append(pendingLabel, pendingText);

    const pendingAnswer = document.createElement("div");
    pendingAnswer.className = "ai-answer";
    const pendingAnswerLabel = document.createElement("strong");
    pendingAnswerLabel.textContent = "CourseMind AI:";
    const pendingAnswerText = document.createElement("p");
    pendingAnswerText.textContent = "Thinking through the lecture content…";
    pendingAnswer.append(pendingAnswerLabel, pendingAnswerText);
    pendingMessage.append(pendingQuestion, pendingAnswer);
    chatHistoryContainer.appendChild(pendingMessage);
    pendingMessage.scrollIntoView({ behavior: "smooth", block: "nearest" });


    console.log(
        "Sending question to CourseMind..."
    );

    console.log(
        "Video ID:",
        videoId
    );

    console.log(
        "Question:",
        question
    );

    console.log(
        "Chat history:",
        chatHistory
    );


    /* =================================================
       SEND QUESTION TO BACKEND
    ================================================= */

    try {

        const response =
            await fetch(
                "http://127.0.0.1:8000/ask",
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify({

                        video_id:
                            videoId,

                        question:
                            question,

                        history:
                            chatHistory

                    })

                }
            );


        console.log(
            "Backend status:",
            response.status
        );


        /* -------------------------------------------------
           GET BACKEND RESPONSE
        ------------------------------------------------- */

        const data =
            await response.json();


        console.log(
            "Backend response:",
            data
        );


        /* -------------------------------------------------
           CHECK BACKEND ERROR
        ------------------------------------------------- */

        if (!response.ok) {

            throw new Error(
                data.error ||
                data.message ||
                "Failed to get answer"
            );

        }


        /* =================================================
           GET ANSWER
        ================================================= */

        const answer =
            data.answer ||
            "No answer was generated.";


        /* =================================================
           SAVE CHAT HISTORY
        ================================================= */

        chatHistory.push({

            question:
                question,

            answer:
                answer

        });


        console.log(
            "Updated chat history:",
            chatHistory
        );


        /* =================================================
           CREATE CHAT MESSAGE
        ================================================= */

        pendingMessage.remove();
        createChatMessage(
            question,
            answer,
            data.sources
        );


        /* -------------------------------------------------
           CLEAR INPUT
        ------------------------------------------------- */

        questionInput.value =
            "";


        /* -------------------------------------------------
           SCROLL TO NEW ANSWER
        ------------------------------------------------- */

        chatHistoryContainer.lastElementChild.scrollIntoView({

            behavior: "smooth",

            block: "nearest"

        });


        /* =================================================
           PRINT SOURCES
        ================================================= */

        console.log(
            "========== SOURCES =========="
        );


        if (data.sources) {

            data.sources.forEach(
                function(source) {

                    console.log(
                        `Chunk ${source.chunk_id} | Similarity: ${source.similarity}`
                    );

                }
            );

        }


    } catch (error) {

        /* =================================================
           ERROR
        ================================================= */

        console.error(
            "AI request failed:",
            error
        );


        pendingMessage.remove();
        aiError.textContent =
            "CourseMind could not generate an answer.\n\n" +
            error.message;
        aiError.style.display = "block";

    }


    /* =================================================
       ENABLE BUTTON
    ================================================= */

    askAI.disabled =
        false;

    askAI.textContent =
        "Ask AI";

}


/* =====================================================
   CREATE CHAT MESSAGE
===================================================== */

function createChatMessage(
    question,
    answer,
    sources
) {

    /* -------------------------------------------------
       MAIN CHAT MESSAGE
    ------------------------------------------------- */

    const message =
        document.createElement(
            "div"
        );


    message.className =
        "chat-message";


    /* =================================================
       QUESTION
    ================================================= */

    const questionDiv =
        document.createElement(
            "div"
        );


    questionDiv.className =
        "ai-question";


    const questionStrong =
        document.createElement(
            "strong"
        );


    questionStrong.textContent =
        "You:";


    const questionText =
        document.createElement(
            "span"
        );


    questionText.textContent =
        ` ${question}`;


    questionDiv.appendChild(
        questionStrong
    );


    questionDiv.appendChild(
        questionText
    );


    /* =================================================
       ANSWER
    ================================================= */

    const answerDiv =
        document.createElement(
            "div"
        );


    answerDiv.className =
        "ai-answer";


    const answerStrong =
        document.createElement(
            "strong"
        );


    answerStrong.textContent =
        "CourseMind AI:";


    const answerText =
        document.createElement(
            "p"
        );


    answerText.textContent =
        answer;


    answerDiv.appendChild(
        answerStrong
    );


    answerDiv.appendChild(
        answerText
    );


    /* =================================================
       SOURCES
    ================================================= */

    const sourcesDiv =
        document.createElement(
            "div"
        );


    sourcesDiv.className =
        "ai-sources";


    const sourcesStrong =
        document.createElement(
            "strong"
        );


    sourcesStrong.textContent =
        "Sources:";


    sourcesDiv.appendChild(
        sourcesStrong
    );


    /* -------------------------------------------------
       IF SOURCES EXIST
    ------------------------------------------------- */

    if (
        sources &&
        sources.length > 0
    ) {

        sources.forEach(
            function(source) {

                const sourceElement =
                    document.createElement(
                        "span"
                    );


                sourceElement.className =
                    "source-item";


                const similarity =
                    Number(
                        source.similarity
                    );


                sourceElement.textContent =
                    `Chunk ${source.chunk_id} · ${similarity.toFixed(4)}`;


                sourcesDiv.appendChild(
                    sourceElement
                );

            }
        );


    } else {

        const noSources =
            document.createElement(
                "span"
            );


        noSources.textContent =
            "No sources available.";


        sourcesDiv.appendChild(
            noSources
        );

    }


    /* =================================================
       ADD EVERYTHING TO MESSAGE
    ================================================= */

    message.appendChild(
        questionDiv
    );


    message.appendChild(
        answerDiv
    );


    message.appendChild(
        sourcesDiv
    );


    /* =================================================
       ADD MESSAGE TO CHAT HISTORY
    ================================================= */

    chatHistoryContainer.appendChild(
        message
    );

}

/* =====================================================
   LOAD LECTURE SUMMARY
===================================================== */

async function loadLectureSummary() {

    const summaryContainer =
        document.getElementById(
            "lectureSummary"
        );

    if (!summaryContainer) {
        return;
    }

    summaryContainer.innerHTML =
        `<div class="summary-loading">
            Generating lecture summary...
        </div>`;

    try {

        console.log(
            "Loading lecture summary..."
        );

        console.log(
            "Video ID:",
            videoId
        );

        const response =
            await fetch(
                `http://127.0.0.1:8000/summary/${videoId}`
            );

        const data =
            await response.json();

        console.log(
            "Summary response:",
            data
        );

        if (!response.ok) {

            throw new Error(
                data.error ||
                data.message ||
                "Failed to generate summary"
            );

        }

        if (!data.summary) {

            throw new Error(
                "No summary was generated."
            );

        }

        summaryContainer.innerHTML = "";

        const summary =
            document.createElement(
                "div"
            );

        summary.className =
            "summary-content";

        summary.textContent =
            data.summary;

        summaryContainer.appendChild(
            summary
        );

    } catch (error) {

        console.error(
            "Summary error:",
            error
        );

        summaryContainer.innerHTML =
            `<div class="ai-error">
                Could not generate lecture summary.
                <br><br>
                ${error.message}
            </div>`;

    }

}