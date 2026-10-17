const API_URL = 'http://127.0.0.1:8000';

let lectures = [];
let selectedLecture = null;


/* =========================================================
   COURSE API
========================================================= */

async function fetchCourseInfo(url) {

    const response = await fetch(
        `${API_URL}/course/info`,
        {
            method: 'POST',

            headers: {
                'Content-Type': 'application/json'
            },

            body: JSON.stringify({
                url: url
            })
        }
    );

    if (!response.ok) {
        throw new Error(
            `Failed to fetch course information: ${response.status}`
        );
    }

    return await response.json();
}


/* =========================================================
   TOAST
========================================================= */

const toast = document.getElementById('toast');

function show(msg) {

    if (!toast) return;

    toast.textContent = msg;

    toast.classList.add('show');

    clearTimeout(window.tt);

    window.tt = setTimeout(() => {

        toast.classList.remove('show');

    }, 2200);
}


/* =========================================================
   NAVIGATION
========================================================= */

function goToOnboarding() {

    window.location.href = 'onboarding.html';

}


/* =========================================================
   YOUTUBE URL VALIDATION
========================================================= */

function isYoutubeUrl(value) {

    try {

        const u = new URL(value);

        return (
            /(^|\.)youtube\.com$/.test(u.hostname) ||
            /(^|\.)youtu\.be$/.test(u.hostname)
        );

    } catch {

        return false;

    }
}


/* =========================================================
   COURSE STORAGE
========================================================= */


/*
    Get all saved courses
*/
function getSavedCourses() {

    const data =
        localStorage.getItem(
            'coursemind.courses'
        );

    if (data) {

        try {

            const courses =
                JSON.parse(data);

            if (Array.isArray(courses)) {

                return courses;

            }

        } catch {

            // Continue to migration below

        }

    }


    /*
        -----------------------------------------------------
        MIGRATE OLD SINGLE COURSE
        -----------------------------------------------------

        Older version of CourseMind stored the course in:

            coursemind.course

        If it exists, move it into the new
        courses array.
    */

    const oldData =
        localStorage.getItem(
            'coursemind.course'
        );

    if (!oldData) {

        return [];

    }


    try {

        const oldCourse =
            JSON.parse(oldData);


        if (!oldCourse) {

            return [];

        }


        /*
            Create an ID for the old course
        */

        const courseId =
            oldCourse.playlist_id ||
            oldCourse.url ||
            `course_${Date.now()}`;


        const migratedCourse = {

            ...oldCourse,

            courseId: courseId,

            addedAt:
                oldCourse.addedAt ||
                new Date().toISOString()

        };


        const courses = [
            migratedCourse
        ];


        /*
            Save new format
        */

        localStorage.setItem(

            'coursemind.courses',

            JSON.stringify(courses)

        );


        /*
            Set migrated course as active
        */

        localStorage.setItem(

            'coursemind.activeCourseId',

            courseId

        );


        /*
            Keep old data for now.

            We are intentionally NOT deleting it
            until the new system is tested.
        */


        return courses;


    } catch {

        return [];

    }

}


/*
    Get currently active course
*/
function getSavedCourse() {

    const courses =
        getSavedCourses();


    if (!courses.length) {

        return null;

    }


    const activeCourseId =
        localStorage.getItem(
            'coursemind.activeCourseId'
        );


    /*
        Find selected course
    */

    if (activeCourseId) {

        const activeCourse =
            courses.find(

                course =>
                    course.courseId ===
                    activeCourseId

            );


        if (activeCourse) {

            return activeCourse;

        }

    }


    /*
        Fallback:
        first course
    */

    localStorage.setItem(

        'coursemind.activeCourseId',

        courses[0].courseId

    );


    return courses[0];

}


/*
    Save a course
*/
function saveCourse(courseInfo) {

    /*
        Get existing courses
    */

    const courses =
        getSavedCourses();


    /*
        Identify course

        Playlist ID is preferred because
        it uniquely identifies a YouTube playlist.
    */

    const courseId =
        courseInfo.playlist_id ||
        courseInfo.url ||
        `course_${Date.now()}`;


    const newCourse = {

        ...courseInfo,

        courseId: courseId,

        addedAt:
            courseInfo.addedAt ||
            new Date().toISOString()

    };


    /*
        Check whether this course
        already exists
    */

    const existingIndex =
        courses.findIndex(

            course =>
                course.courseId ===
                courseId

        );


    if (existingIndex !== -1) {

        /*
            Update existing course
        */

        courses[existingIndex] =
            newCourse;

    } else {

        /*
            Add new course
        */

        courses.push(
            newCourse
        );

    }


    /*
        Save all courses
    */

    localStorage.setItem(

        'coursemind.courses',

        JSON.stringify(courses)

    );


    /*
        Make newly added course
        the active course
    */

    localStorage.setItem(

        'coursemind.activeCourseId',

        courseId

    );


    /*
        Keep compatibility with
        the existing dashboard checks.
    */

    localStorage.setItem(

        'coursemind.hasCourse',

        'true'

    );

}


/*
    Change active course
*/
function setActiveCourse(courseId) {

    const courses =
        getSavedCourses();


    const course =
        courses.find(

            item =>
                item.courseId ===
                courseId

        );


    if (!course) {

        return false;

    }


    localStorage.setItem(

        'coursemind.activeCourseId',

        courseId

    );


    return true;

}


/* =========================================================
   CONVERT API VIDEOS
   → DASHBOARD LECTURES
========================================================= */

function getLecturesFromCourse(course) {

    if (!course?.videos) {
        return [];
    }

    const completedLectures =
        JSON.parse(
            localStorage.getItem(
                'coursemind.completedLectures'
            )
        ) || [];


    return course.videos.map(
        (video, index) => {

            let status = '';


            /*
                Check if lecture is completed
            */

            if (
                completedLectures.includes(
                    video.video_id
                )
            ) {

                status = 'done';

            }


            /*
                Otherwise check if this is
                the first incomplete lecture
            */

            else {

                const firstIncomplete =
                    course.videos.find(
                        v =>
                            !completedLectures.includes(
                                v.video_id
                            )
                    );

                if (
                    firstIncomplete &&
                    firstIncomplete.video_id ===
                        video.video_id
                ) {

                    status =
                        'progress-status';

                }

            }


            return {

                id: video.video_id,

                n: String(index + 1)
                    .padStart(2, '0'),

                t: video.title,

                d: '-- mins',

                s: status

            };

        }
    );
}

/* =========================================================
   RENDER LECTURES
========================================================= */

let lecturePage = 0;
const LECTURES_PER_PAGE = 8;
let renderedLectureList = lectures;

function render(list = lectures) {
    const grid = document.getElementById('lectures');
    if (!grid) return;

    renderedLectureList = Array.isArray(list) ? list : [];
    const total = renderedLectureList.length;
    const pageCount = Math.max(1, Math.ceil(total / LECTURES_PER_PAGE));
    lecturePage = Math.min(Math.max(lecturePage, 0), pageCount - 1);

    const pagination = document.getElementById('lecturePagination');
    const pageInfo = document.getElementById('lecturePageInfo');
    const prev = document.getElementById('lecturePrev');
    const next = document.getElementById('lectureNext');

    if (!total) {
        grid.innerHTML = `<div style="grid-column:1/-1;text-align:center;color:#a3a3a3;padding:25px;">No lectures found.</div>`;
        if (pagination) pagination.style.display = 'none';
        return;
    }

    const pageStart = lecturePage * LECTURES_PER_PAGE;
    const pageItems = renderedLectureList.slice(pageStart, pageStart + LECTURES_PER_PAGE);

    grid.innerHTML = pageItems.map(x => `
        <article class="lecture" data-id="${x.id}">
            <div class="lecture-img">
                <img src="https://img.youtube.com/vi/${x.id}/hqdefault.jpg" alt="" loading="lazy">
                <span class="num">${x.n}</span>
            </div>
            <div class="lecture-body">
                <h3>${x.t}</h3>
                <div class="lecture-meta">
                    <span>◷ ${x.d}</span>
                    <span class="status ${x.s}">${x.s === 'done' ? '✓' : x.s === 'next' ? '▶' : ''}</span>
                </div>
            </div>
        </article>
    `).join('');

    if (pagination) pagination.style.display = pageCount > 1 ? 'flex' : 'none';
    if (pageInfo) {
        pageInfo.textContent = `Showing ${pageStart + 1}–${Math.min(pageStart + LECTURES_PER_PAGE, total)} of ${total} lectures · Page ${lecturePage + 1} of ${pageCount}`;
    }
    if (prev) prev.disabled = lecturePage === 0;
    if (next) {
        next.disabled = lecturePage >= pageCount - 1;
        next.textContent = lecturePage >= pageCount - 1 ? 'Last page' : 'Next 8 →';
    }
}


/* =========================================================
   SELECT LECTURE
========================================================= */

function selectLecture(lecture) {

    if (!lecture) return;


    /*
        Save selected lecture
    */

    selectedLecture = lecture;

    localStorage.setItem(
        'coursemind.selectedLecture',

        JSON.stringify(lecture)
    );


    /*
        Debug
    */

    console.log(
        'Selected lecture:',
        lecture
    );


    /*
        Open lecture page
    */

    window.location.href =
        `lecture.html?id=${encodeURIComponent(
            lecture.id
        )}`;

}


/* =========================================================
   AI CHAT
========================================================= */

function addBubble(text, cls) {

    const chat =
        document.getElementById(
            'chat'
        );

    if (!chat) return;


    const d =
        document.createElement(
            'div'
        );


    d.className =
        `bubble ${cls}`;


    d.textContent = text;
    d.setAttribute('role', cls === 'user' ? 'status' : 'article');

    chat.appendChild(d);
    chat.scrollTop = chat.scrollHeight;

}


/* =========================================================
   ASK AI
========================================================= */


/* FULL-SCREEN CHAT HELPERS */
let fullChatBusy = false;
let fullChatHistory = [];
let fullChatHistoryCourseId = null;
function openFullChat(initialQuestion = '') {
  const overlay = document.getElementById('chatOverlay');
  if (!overlay) return;
  overlay.classList.add('is-open');
  overlay.setAttribute('aria-hidden','false');
  document.body.classList.add('cm-chat-open');
  const course = getSavedCourse();
  const context = document.getElementById('chatContext');
  if (context) context.textContent = course ? `Active course: ${course.name || course.title || 'Untitled course'}` : 'Add a course to ask course-specific questions.';
  if (initialQuestion) submitFullChatQuestion(initialQuestion);
  else setTimeout(() => document.getElementById('fullChatQuestion')?.focus(), 100);
}
function closeFullChat() {
  const overlay = document.getElementById('chatOverlay');
  if (!overlay) return;
  overlay.classList.remove('is-open');
  overlay.setAttribute('aria-hidden','true');
  document.body.classList.remove('cm-chat-open');
}
function appendFullChatMessage(text, who, extraClass = '') {
  const messages = document.getElementById('fullChatMessages');
  if (!messages) return null;
  document.getElementById('fullChatWelcome')?.remove();
  const row = document.createElement('div');
  row.className = `cm-chat-message ${who}${extraClass ? ` ${extraClass}` : ''}`;
  const avatar = document.createElement('div');
  avatar.className = 'cm-chat-avatar'; avatar.textContent = who === 'user' ? 'You' : '✦';
  const bubble = document.createElement('div');
  bubble.className = 'cm-chat-bubble'; bubble.textContent = text;
  row.append(avatar,bubble); messages.appendChild(row); messages.scrollTop = messages.scrollHeight;
  return {row,bubble};
}
function setFullChatBusy(busy) {
  fullChatBusy = busy;
  const button = document.getElementById('fullChatSend');
  const input = document.getElementById('fullChatQuestion');
  if (button) button.disabled = busy;
  if (input) input.disabled = busy;
}
async function submitFullChatQuestion(value) {
  const question = String(value || '').trim();
  if (!question || fullChatBusy) return;
  const input = document.getElementById('fullChatQuestion');
  if (input) input.value = '';
  appendFullChatMessage(question,'user');
  const pending = appendFullChatMessage('Thinking through your course...','assistant','pending');
  setFullChatBusy(true);
  try {
    const course = getSavedCourse();
    if (!course) throw new Error('Please add and select a course first.');
    const playlistId = course.playlist_id || course.courseId;
    if (!playlistId) throw new Error('The selected course has no playlist ID.');
    if (fullChatHistoryCourseId !== playlistId) {
      fullChatHistory = [];
      fullChatHistoryCourseId = playlistId;
    }
    const response = await fetch(`${API_URL}/ask/course`, {
      method:'POST', headers:{'Content-Type':'application/json'},
      body:JSON.stringify({playlist_id:playlistId,question,top_k:5,history:fullChatHistory.slice(-8)})
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || data.message || `Request failed: ${response.status}`);
    pending?.row.remove();
    const answer = data.answer || data.message || "I couldn't generate an answer from this course.";
    if (typeof data.answer === 'string' && data.answer.trim()) {
      fullChatHistory.push({question, answer: data.answer});
      if (fullChatHistory.length > 8) fullChatHistory = fullChatHistory.slice(-8);
    }
    const message = appendFullChatMessage('','assistant');
    if (message) {
      answer.split(/\n{2,}/).filter(Boolean).forEach(part => {
        const p = document.createElement('p'); p.textContent = part; message.bubble.appendChild(p);
      });
      if (Array.isArray(data.sources) && data.sources.length) {
        const unique = [...new Map(data.sources.map(s => [s.video_id,s])).values()];
        const sources = document.createElement('div'); sources.className = 'cm-chat-sources';
        sources.textContent = `Sources: ${unique.map(s => s.video_title).filter(Boolean).join(' · ')}`;
        message.bubble.appendChild(sources);
      }
    }
    addBubble(question,'user'); addBubble(answer,'ai-msg');
  } catch (error) {
    console.error('Full-screen CourseMind chat failed:',error);
    pending?.row.remove();
    appendFullChatMessage(error.message || "I couldn't reach the course AI tutor. Check that FastAPI is running and try again.",'assistant');
  } finally {
    setFullChatBusy(false); input?.focus();
  }
}

async function ask(q) {
    if (!q?.trim()) return;

    const question = q.trim();

    // Get the currently selected course.
    const course = getSavedCourse();

    if (!course) {
        addBubble(
            "Please add and select a course first.",
            "ai-msg"
        );
        return;
    }

    const playlistId =
        course.playlist_id ||
        course.courseId;

    if (!playlistId) {
        addBubble(
            "The selected course has no playlist ID. Please check your saved course information.",
            "ai-msg"
        );
        return;
    }

    // Display the user's question.
    addBubble(question, "user");

    // Display a temporary loading message.
    addBubble("Thinking through your course...", "ai-msg");

    const chat = document.getElementById("chat");
    const loadingBubble = chat?.lastElementChild;
    if (loadingBubble) loadingBubble.classList.add("loading-bubble");

    try {
        const response = await fetch(
            `${API_URL}/ask/course`,
            {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    playlist_id: playlistId,
                    question: question,
                    top_k: 5,
                    history: []
                })
            }
        );

        const data = await response.json();

        if (!response.ok) {
            throw new Error(
                data.detail ||
                data.message ||
                `Request failed: ${response.status}`
            );
        }

        if (loadingBubble) {
            loadingBubble.remove();
        }

        if (data.answer) {
            addBubble(data.answer, "ai-msg");
        } else {
            addBubble(
                data.message ||
                "I couldn't generate an answer from this course.",
                "ai-msg"
            );
        }

        // Show the source lectures returned by the backend.
        if (Array.isArray(data.sources) && data.sources.length) {
            const uniqueSources = [
                ...new Map(
                    data.sources.map(source => [
                        source.video_id,
                        source
                    ])
                ).values()
            ];

            const sourceText = uniqueSources
                .map(source => source.video_title)
                .join("\n");

            addBubble(
                `Sources:\n${sourceText}`,
                "ai-msg"
            );
        }

    } catch (error) {
        console.error("Course AI request failed:", error);

        if (loadingBubble) {
            loadingBubble.remove();
        }

        addBubble(
            "I couldn't reach the course AI tutor. Please check that the FastAPI server is running and try again.",
            "ai-msg"
        );
    }
}



/* =========================================================
   ONBOARDING PAGE
========================================================= */

if (
    document.body.dataset.page ===
    'onboarding'
) {

    const form =
        document.getElementById(
            'courseForm'
        );


    const urlInput =
        document.getElementById(
            'courseUrl'
        );


    const nameInput =
        document.getElementById(
            'courseName'
        );


    /* -----------------------------------------------------
       ADD COURSE
    ----------------------------------------------------- */

    form?.addEventListener(
        'submit',

        async e => {

            e.preventDefault();


            const url =
                urlInput.value.trim();


            /*
                Validate URL
            */

            if (!isYoutubeUrl(url)) {

                show(
                    'Please enter a valid YouTube URL.'
                );

                urlInput.focus();

                return;

            }


            try {

                show(
                    'Analyzing your course...'
                );


                /*
                    Get playlist information
                    from FastAPI
                */

                const courseInfo =
                    await fetchCourseInfo(
                        url
                    );


                console.log(
                    'Course information:',
                    courseInfo
                );


                /*
                    Check API response
                */

                if (
                    !courseInfo.videos
                ) {

                    throw new Error(

                        courseInfo.message ||
                        'Could not fetch course information'

                    );

                }


                /*
                    Save complete course
                    information
                */

                saveCourse({

                    ...courseInfo,

                    url: url,

                    name:
                        nameInput.value.trim() ||
                        courseInfo.title

                });


                show(

                    `Course added — ${courseInfo.total_videos} lectures found.`

                );


                /*
                    Open dashboard
                */

                setTimeout(() => {

                    window.location.href =
                        'index.html';

                }, 1000);


            } catch (error) {

                console.error(
                    'Course loading failed:',
                    error
                );


                show(
                    'Could not process this course. Please try again.'
                );

            }

        }
    );


    /* -----------------------------------------------------
       DEMO COURSE
    ----------------------------------------------------- */

    document
        .getElementById('demo')
        ?.addEventListener(

            'click',

            async () => {

                const url =
                    'https://www.youtube.com/playlist?list=PLfqMhTWNBTe137I_EPQd34TsgV6IO55pt';


                try {

                    show(
                        'Loading demo course...'
                    );


                    const courseInfo =
                        await fetchCourseInfo(
                            url
                        );


                    console.log(
                        'Demo course information:',
                        courseInfo
                    );


                    saveCourse({

                        ...courseInfo,

                        url: url,

                        name:
                            'DSA Series by Shradha Khapra Ma’am'

                    });


                    window.location.href =
                        'index.html';


                } catch (error) {

                    console.error(
                        'Demo course failed:',
                        error
                    );


                    show(
                        'Could not load demo course.'
                    );

                }

            }

        );

}


/* =========================================================
   EXISTING USER DASHBOARD
========================================================= */

if (
    document.body.dataset.page ===
    'dashboard'
) {

    /* -----------------------------------------------------
    LOAD COURSES AND INITIALIZE SELECTOR
    ----------------------------------------------------- */

    const courses = getSavedCourses();

    let course = getSavedCourse();

    console.log(
        'Saved course:',
        course
    );

    const courseSelector =
        document.getElementById('courseSelector');


    /* Populate course dropdown */

    if (courseSelector) {

        courseSelector.innerHTML = courses.map(item => `
            <option value="${item.courseId}">
                ${item.name || item.title || 'Untitled course'}
            </option>
        `).join('');

        if (course) {
            courseSelector.value = course.courseId;
        }
    }


    /* -----------------------------------------------------
    DISPLAY ACTIVE COURSE
    ----------------------------------------------------- */

    function displayActiveCourse() {

        if (!course) {
            show('No saved courses found.');
            return;
        }

        const videos = course.videos || [];

        document.getElementById('currentCourseTitle').textContent =
            course.name || course.title || 'Untitled course';

        document.getElementById('currentCourseMeta').textContent =
            `${videos.length} Lectures`;

        document.getElementById('currentCourseDescription').textContent =
            course.description ||
            'Learn from the videos in this YouTube course.';

        const image =
            document.getElementById('currentCourseImage');

        if (image) {
            image.src = videos.length
                ? `https://img.youtube.com/vi/${videos[0].video_id}/hqdefault.jpg`
                : '';

            image.alt = course.name || course.title || 'Course thumbnail';
        }

        const count =
            document.getElementById('currentCourseLectureCount');

        if (count) {
            count.textContent = `${videos.length} lectures`;
        }

        const progressText =
            document.getElementById('currentCourseProgressText');

        if (progressText) {
            progressText.textContent = 'Not tracked yet';
        }

        const progressFill =
            document.getElementById('currentCourseProgressFill');

        if (progressFill) {
            progressFill.style.width = '0%';
        }
    }


    /* -----------------------------------------------------
    LOAD ACTIVE COURSE LECTURES
    ----------------------------------------------------- */

    function loadActiveCourse() {

        course = getSavedCourse();

        lectures = getLecturesFromCourse(course);

        displayActiveCourse();

        render(lectures);

        console.log('Active course:', course);
        console.log('Lectures loaded:', lectures.length);
    }


    /* Initial load */

    loadActiveCourse();


    /* -----------------------------------------------------
    SWITCH ACTIVE COURSE
    ----------------------------------------------------- */

    courseSelector?.addEventListener('change', () => {

        const selectedId = courseSelector.value;

        if (!setActiveCourse(selectedId)) {
            show('Could not select this course.');
            return;
        }

        loadActiveCourse();

        show('Course switched successfully.');

    });



    /* -----------------------------------------------------
       CONVERT VIDEOS → LECTURES
    ----------------------------------------------------- */

    lectures =
        getLecturesFromCourse(
            course
        );


    console.log(
        'Lectures loaded:',
        lectures
    );

    /* =====================================================
    COURSE PROGRESS
    ===================================================== */

        const completedLectures =
            JSON.parse(
                localStorage.getItem(
                    'coursemind.completedLectures'
                )
            ) || [];


        const totalLectures =
            course?.videos?.length || 0;


        const completedCount =
            completedLectures.filter(
                id =>
                    course.videos.some(
                        video =>
                            video.video_id === id
                    )
            ).length;


        const progressPercent =
            totalLectures > 0
                ? Math.round(
                    (completedCount /
                        totalLectures) * 100
                )
                : 0;


        /* Update completed count */

        const completedElement =
            document.getElementById(
                'completedCount'
            );

        if (completedElement) {

            completedElement.textContent =
                completedCount;

        }


        /* Update percentage */

        const percentElement =
            document.getElementById(
                'progressPercent'
            );

        if (percentElement) {

            percentElement.textContent =
                `${progressPercent}% Complete`;

        }


        /* Update lecture count */

        const lectureCountElement =
            document.getElementById(
                'progressLectures'
            );

        if (lectureCountElement) {

            lectureCountElement.textContent =
                `${completedCount} / ${totalLectures} lectures`;

        }

    /* -----------------------------------------------------
       RENDER LECTURES
    ----------------------------------------------------- */

    render(
        lectures
    );


    /* =====================================================
       LECTURE PAGINATION
    ===================================================== */

    document.getElementById('lecturePrev')?.addEventListener('click', () => {
        if (lecturePage > 0) {
            lecturePage--;
            render(renderedLectureList);
            document.getElementById('lectures')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
    });

    document.getElementById('lectureNext')?.addEventListener('click', () => {
        const pageCount = Math.ceil(renderedLectureList.length / LECTURES_PER_PAGE);
        if (lecturePage < pageCount - 1) {
            lecturePage++;
            render(renderedLectureList);
            document.getElementById('lectures')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
    });

    /* =====================================================
       SEARCH
    ===================================================== */

    document
        .getElementById('search')
        ?.addEventListener(

            'input',

            e => {

                const q =
                    e.target.value
                        .toLowerCase()
                        .trim();


                const filtered =
                    q

                        ? lectures.filter(
                            x =>
                                x.t
                                    .toLowerCase()
                                    .includes(q)
                        )

                        : lectures;


                lecturePage = 0;
                render(filtered);

            }

        );


    /* =====================================================
       ADD NEW COURSE
    ===================================================== */

    document
        .getElementById('addCourseTop')
        ?.addEventListener(
            'click',
            goToOnboarding
        );


    document
        .getElementById('manageCourses')
        ?.addEventListener(
            'click',
            goToOnboarding
        );


    /* =====================================================
       PROMO CARD
    ===================================================== */

    document
        .getElementById('promo')
        ?.addEventListener(

            'click',

            () => {

                show(
                    'CourseMind turns course videos into searchable learning content.'
                );

            }

        );


    /* =====================================================
       CONTINUE LEARNING
    ===================================================== */

    document
        .getElementById('continue')
        ?.addEventListener(

            'click',

            () => {

                if (!lectures.length) {

                    show(
                        'No lectures available.'
                    );

                    return;

                }


                /*
                    Find current lecture

                    Otherwise use first lecture
                */

                const current =
                    lectures.find(
                        x =>
                            x.s ===
                            'progress-status'
                    ) ||
                    lectures[0];


                /*
                    Open current lecture
                */

                selectLecture(
                    current
                );

            }

        );


    /* =====================================================
       VIEW ALL
    ===================================================== */

    document
        .getElementById('all')
        ?.addEventListener(

            'click',

            () => {

                show(
                    `All ${lectures.length} lectures are available.`
                );

            }

        );


    /* FULL-SCREEN CHAT EVENTS */
    document.getElementById('question')?.addEventListener('focus', () => openFullChat());
    document.getElementById('chatForm')?.addEventListener('submit', e => {
      e.preventDefault();
      const value = document.getElementById('question')?.value || '';
      openFullChat();
      if (value.trim()) submitFullChatQuestion(value);
      const compact = document.getElementById('question'); if (compact) compact.value = '';
    });
    document.getElementById('closeChat')?.addEventListener('click',closeFullChat);
    document.getElementById('chatBackdrop')?.addEventListener('click',closeFullChat);
    document.getElementById('clearChat')?.addEventListener('click',() => {
      fullChatHistory = [];
      fullChatHistoryCourseId = null;
      const messages = document.getElementById('fullChatMessages');
      if (messages) messages.innerHTML = `<div class="cm-chat-welcome" id="fullChatWelcome">
        <div class="cm-chat-welcome-icon">✦</div><h2>What would you like to learn?</h2>
        <p>Ask a question about your course. I'll use the available lecture content to help you understand it.</p>
        <div class="cm-chat-suggestions">
        <button type="button" data-full-q="Explain the most important concepts in this course">Explain key concepts <span>↗</span></button>
        <button type="button" data-full-q="Give me a summary of this course">Summarize this course <span>↗</span></button>
        <button type="button" data-full-q="Quiz me on the topics covered in this course">Quiz me <span>↗</span></button></div></div>`;
    });
    document.getElementById('fullChatForm')?.addEventListener('submit',e => {
      e.preventDefault(); submitFullChatQuestion(document.getElementById('fullChatQuestion')?.value || '');
    });
    document.getElementById('fullChatQuestion')?.addEventListener('keydown',e => {
      if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); document.getElementById('fullChatForm')?.requestSubmit(); }
    });
    document.getElementById('fullChatQuestion')?.addEventListener('input',e => {
      e.target.style.height='auto'; e.target.style.height=`${Math.min(e.target.scrollHeight,180)}px`;
    });
    document.addEventListener('click',e => {
      const suggestion=e.target.closest('[data-full-q]');
      if (suggestion && document.getElementById('chatOverlay')?.classList.contains('is-open')) submitFullChatQuestion(suggestion.dataset.fullQ);
    });
    document.addEventListener('keydown',e => { if (e.key === 'Escape') closeFullChat(); });

    /* =====================================================
       CLICK HANDLING
    ===================================================== */

    document.addEventListener(

        'click',

        e => {


            /* -------------------------------------------------
               LECTURE CARD
            ------------------------------------------------- */

            const card =
                e.target.closest(
                    '.lecture'
                );


            if (card) {

                const lecture =
                    lectures.find(
                        v =>
                            v.id ===
                            card.dataset.id
                    );


                if (lecture) {

                    console.log(
                        'Opening lecture:',
                        lecture
                    );


                    selectLecture(
                        lecture
                    );

                }


                /*
                    Important:

                    Stop here so the same click
                    does not trigger other handlers.
                */

                return;

            }


            /* -------------------------------------------------
               AI SUGGESTED QUESTION
            ------------------------------------------------- */

            const q =
                e.target.closest(
                    '[data-q]'
                );


            if (q) {
                openFullChat(q.dataset.q);
                return;
            }


            /* -------------------------------------------------
               SIDEBAR NAVIGATION
            ------------------------------------------------- */

            const nav =
                e.target.closest(
                    '.nav'
                );


            if (nav) {


                document
                    .querySelectorAll(
                        '.nav'
                    )
                    .forEach(
                        n =>
                            n.classList.remove(
                                'active'
                            )
                    );


                nav.classList.add(
                    'active'
                );


                if (
                    nav.dataset.nav !==
                    'Dashboard'
                ) {

                    show(

                        `${nav.dataset.nav} module — coming next.`

                    );

                }


                return;

            }


            /* -------------------------------------------------
               FEATURE CARDS
            ------------------------------------------------- */

            const feature =
                e.target.closest(
                    '.feature'
                );


            if (feature) {

                show(
                    'This module will be connected next.'
                );

                return;

            }

        }

    );


    /* =====================================================
       CTRL + K SEARCH
    ===================================================== */

    document.addEventListener(

        'keydown',

        e => {

            if (

                (e.ctrlKey || e.metaKey) &&

                e.key.toLowerCase() === 'k'

            ) {

                e.preventDefault();


                const search =
                    document.getElementById(
                        'search'
                    );


                if (search) {

                    search.focus();

                    search.select();

                }

            }

        }

    );

}