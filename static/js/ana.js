$(".sidebar-dropdown > a").click(function() {
    $(".sidebar-submenu").slideUp(200);
    if (
      $(this)
        .parent()
        .hasClass("active")
    ) {
      $(".sidebar-dropdown").removeClass("active");
      $(this)
        .parent()
        .removeClass("active");
    } else {
      $(".sidebar-dropdown").removeClass("active");
      $(this)
        .next(".sidebar-submenu")
        .slideDown(200);
      $(this)
        .parent()
        .addClass("active");
    }
  });
  
  $("#close-sidebar").click(function() {
    $(".page-wrapper").removeClass("toggled");
  });
  $("#show-sidebar").click(function() {
    $(".page-wrapper").addClass("toggled");
  });
  
  const circularProgress = document.querySelectorAll(".circular-progress");

  Array.from(circularProgress).forEach((progressBar) => {
    const progressValue = progressBar.querySelector(".percentage");
    const innerCircle = progressBar.querySelector(".inner-circle");
    let startValue = 0,
      endValue = Number(progressBar.getAttribute("data-percentage")),
      speed = 50,
      progressColor = progressBar.getAttribute("data-progress-color");
  
    const progress = setInterval(() => {
      startValue++;
      progressValue.textContent = `${startValue}%`;
      progressValue.style.color = `${progressColor}`;
  
      innerCircle.style.backgroundColor = `${progressBar.getAttribute(
        "data-inner-circle-color"
      )}`;
  
      progressBar.style.background = `conic-gradient(${progressColor} ${
        startValue * 3.6
      }deg,${progressBar.getAttribute("data-bg-color")} 0deg)`;
      if (startValue === endValue) {
        clearInterval(progress);
      }
    }, speed);
  });
