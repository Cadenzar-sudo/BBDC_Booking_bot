// dashboard.js
const tableBody = document.querySelector("#dataTable tbody");
const addRowBtn = document.getElementById("addRowBtn");
const saveBtn = document.getElementById("saveBtn");

// Helper: month code (YYYYMM) -> human label like "Jan 2025"
const MONTH_NAMES = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
function formatYYYYMM(yyyymm) {
  if (!yyyymm || yyyymm.length !== 6) return yyyymm || "";
  const y = yyyymm.slice(0, 4);
  const m = yyyymm.slice(4, 6);
  const idx = Number(m) - 1;
  return `${MONTH_NAMES[idx] ?? m} ${y}`;
}

// Create a new row. Optionally pass job object to preload values.
function createRow(job = {}) {
  const row = document.createElement("tr");

  // defaults
  const defaultBuffer = job.buffer ?? 130;
  const defaultReloadTime = job.reload_time ?? 10;
  const defaultNoOfReloads = job.no_of_reloads ?? 250;
  const jobTargetMonths = job.target_months ?? []; // array of YYYYMM strings
  const jobStartTimes = job.start_times ?? [];

  row.innerHTML = `
      <td class="p-3 align-top">
        <input type="text" name="username"
               class="border rounded-lg p-2 w-full focus:ring-2 focus:ring-blue-500"
               placeholder="Username" value="${job.username ?? ''}">
      </td>

      <td class="p-3 align-top">
        <input type="password" name="password"
               class="border rounded-lg p-2 w-full focus:ring-2 focus:ring-blue-500"
               placeholder="Password" value="${job.password ?? ''}">
      </td>

      <td class="p-3 start-time-cell align-top">
        <div class="start-times space-y-2"></div>
        <button class="addStartTimeBtn mt-2 px-2 py-1 bg-blue-100 text-blue-700 rounded hover:bg-blue-200">
          + Add time
        </button>
      </td>

      <td class="p-3 months-cell align-top">
        <div class="months-list flex flex-wrap gap-2"></div>
        <div class="mt-2 flex items-center gap-2">
          <input type="month" class="month-input border rounded-lg p-1 w-32 text-sm" />
          <button class="addMonthBtn px-2 py-1 bg-blue-100 text-blue-700 rounded hover:bg-blue-200">+ Add month</button>
        </div>
      </td>

     <td class="p-3 settings-cell align-top">
        <div class="grid grid-cols-1 gap-2">

          <div class="flex items-center gap-2">
            <label class="w-24 text-sm">Buffer</label>
            <input type="number" name="buffer"
                  class="border rounded-lg p-1 w-20"
                  inputmode="numeric"
                  step="1" min="0"
                  value="${defaultBuffer}">
          </div>

          <div class="flex items-center gap-2">
            <label class="w-24 text-sm">Reload Time</label>
            <input type="number" name="reload_time"
                  class="border rounded-lg p-1 w-20"
                  inputmode="numeric"
                  step="1" min="0"
                  value="${defaultReloadTime}">
          </div>

          <div class="flex items-center gap-2">
            <label class="w-24 text-sm">No of Reloads</label>
            <input type="number" name="no_of_reloads"
                  class="border rounded-lg p-1 w-20"
                  inputmode="numeric"
                  step="1" min="0"
                  value="${defaultNoOfReloads}">
          </div>

        </div>
      </td>


      <td class="p-3 align-top pl-8">
        <input type="text" name="description"
               class="border rounded-lg p-2 w-full focus:ring-2 focus:ring-blue-500"
               placeholder="Description" value="${job.description ?? ''}">
      </td>

      <td class="p-3 align-top">
        <button class="deleteRowBtn px-3 py-1 bg-red-500 text-white rounded-lg hover:bg-red-600">
          Delete
        </button>
      </td>
    `;

  // append and wire up dynamic behaviour
  tableBody.appendChild(row);

  // Start times logic
  const startTimesContainer = row.querySelector(".start-times");
  const addStartTimeBtn = row.querySelector(".addStartTimeBtn");

  function addStartTime(value = "") {
    const wrapper = document.createElement("div");
    wrapper.classList.add("start-time-group", "flex", "items-center", "gap-2");

    wrapper.innerHTML = `
          <input type="time" name="start_time[]"
                 class="border rounded-lg p-2 focus:ring-2 focus:ring-blue-500" value="${value}">
          <button class="removeStartTimeBtn bg-red-200 hover:bg-red-300 text-red-700 rounded px-2">×</button>
        `;

    startTimesContainer.appendChild(wrapper);

    wrapper.querySelector(".removeStartTimeBtn").addEventListener("click", () => {
      wrapper.remove();
    });
  }

  // load existing start times
  jobStartTimes.forEach(st => addStartTime(st));

  addStartTimeBtn.addEventListener("click", () => addStartTime());

  // Months logic
  const monthsList = row.querySelector(".months-list");
  const addMonthBtn = row.querySelector(".addMonthBtn");
  const monthInput = row.querySelector(".month-input");

  function addMonth(yyyymm) {
    // ensure no duplicates
    if (!yyyymm) return;
    if (Array.from(monthsList.querySelectorAll(".month-item")).some(el => el.dataset.value === yyyymm)) return;

    const item = document.createElement("div");
    item.className = "month-item inline-flex items-center gap-2 bg-gray-100 px-2 py-1 rounded";
    item.dataset.value = yyyymm;

    const label = document.createElement("span");
    label.className = "text-sm";
    label.textContent = formatYYYYMM(yyyymm);

    const hidden = document.createElement("input");
    hidden.type = "hidden";
    hidden.name = "target_month[]";
    hidden.value = yyyymm;

    const removeBtn = document.createElement("button");
    removeBtn.type = "button";
    removeBtn.className = "removeMonthBtn text-red-600 px-1";
    removeBtn.textContent = "×";

    removeBtn.addEventListener("click", () => item.remove());

    item.appendChild(label);
    item.appendChild(hidden);
    item.appendChild(removeBtn);

    monthsList.appendChild(item);
  }

  // preload months from job (job.target_months expected as ["YYYYMM", ...])
  jobTargetMonths.forEach(ym => addMonth(ym));

  addMonthBtn.addEventListener("click", (e) => {
    e.preventDefault();
    const val = monthInput.value; // "2025-01"
    if (!val) return;
    const parts = val.split("-");
    if (parts.length !== 2) return;
    const yyyymm = parts[0] + parts[1];
    addMonth(yyyymm);
    monthInput.value = ""; // clear
  });

  // Delete row
  row.querySelector(".deleteRowBtn").addEventListener("click", () => {
    row.remove();
  });

  return row;
}

// Add empty row on button click
addRowBtn.addEventListener("click", () => createRow());

// Load data from Jinja payload
(function loadFromJinja() {
  try {
    const raw = document.getElementById('data').textContent;
    const jobs = JSON.parse(raw || "[]");
    // jobs expected to be an array of objects
    if (Array.isArray(jobs)) {
      jobs.forEach(job => createRow(job));
    } else if (typeof jobs === "object" && jobs !== null) {
      // allow object keyed by user
      for (const k in jobs) {
        if (Object.prototype.hasOwnProperty.call(jobs, k)) {
          createRow(jobs[k]);
        }
      }
    }
  } catch (err) {
    console.error("Failed to parse jobs JSON:", err);
  }
})();

// ================================
// SAVE → send to API
// ================================
saveBtn.addEventListener("click", async () => {
  const rows = tableBody.querySelectorAll("tr");
  const data = [];

  rows.forEach(row => {
    const username = row.querySelector('input[name="username"]').value;
    const password = row.querySelector('input[name="password"]').value;
    const description = row.querySelector('input[name="description"]').value;

    // start times
    const startTimes = [];
    row.querySelectorAll('.start-times input[type="time"]').forEach(t => {
      if (t.value) startTimes.push(t.value);
    });

    // target months as YYYYMM (read from hidden inputs)
    const targetMonths = [];
    row.querySelectorAll('input[name="target_month[]"]').forEach(inp => {
      if (inp.value) targetMonths.push(inp.value);
    });

    // settings
    const bufferVal = row.querySelector('input[name="buffer"]').value;
    const reloadTimeVal = row.querySelector('input[name="reload_time"]').value;
    const noOfReloadsVal = row.querySelector('input[name="no_of_reloads"]').value;

    data.push({
      username,
      password,
      start_times: startTimes,
      target_months: targetMonths,
      description,
      buffer: Number(bufferVal) || 0,
      reload_time: Number(reloadTimeVal) || 0,
      no_of_reloads: Number(noOfReloadsVal) || 0
    });
  });

  console.log("Sending to API:", data);

  try {
    const response = await fetch("/api/update", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data)
    });

    // note: check for non-JSON responses
    const text = await response.text();
    let result;
    try {
      result = JSON.parse(text);
    } catch (_) {
      console.warn("Non-JSON response:", text);
      result = text;
    }

    if (!response.ok) {
      console.error("Save error:", result);
      alert("Failed to save data. See console for details.");
      return;
    }

    alert("Saved successfully!");
    console.log("Save result:", result);

  } catch (error) {
    console.error(error);
    alert("Failed to save data.");
  }
});
