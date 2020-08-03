// VanillaJS!!
function update_progress() {
  var status_div = document.querySelector("#status");
  var progress_div = document.querySelector("#progress");
  fetch(status_url)
    .then(function (response) {
      // The API call was successful!
      if (response.ok) {
        return response.json();
      }
      // There was an error
      return Promise.reject(response);
    })
    .then(function (data) {
      // This is the JSON from our response
      status = "Job status: " + data["status"];
      if (data["progress"] == null) {
        progress = "Progress: 0%";
      } else {
        progress = "Progress: " + data["progress"] + "%";
      }

      status_div.textContent = status;
      progress_div.textContent = progress;

      // Checks if the script is finished
      if (data["status"] == "finished") {
        status_div.textContent = status;
        progress_div.textContent = "Progress: 100%";
      } else if (data["status"] == "failed") {
        status_div.textContent = status;
        progress_div.textContent = "Progress: 100%";
      } else {
        setTimeout(function () {
          update_progress();
        }, 800);
      }
    })
    .catch(function (err) {
      // There was an error
      console.warn("Something went wrong.", err);
    });
}
update_progress();
