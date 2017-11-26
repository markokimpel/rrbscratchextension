$(document).ready(function() {

  $("#ledSubmit").click(function() {
    $.ajax({
      method: "POST",
      url: "/v1/led/" + encodeURIComponent($("#ledNo").val()),
      data: JSON.stringify({state: $("#ledState").val()}),
      contentType: "application/json; charset=UTF-8",
      error: function(jqXHR, textStatus, errorThrown) {
        alert("Error: " + errorThrown);
      }
    });
  });

  $("#switchSubmit").click(function() {
    $("#switchState").val("?");
    $.ajax({
      method: "GET",
      url: "/v1/switch/" + encodeURIComponent($("#switchNo").val()),
      dataType: "json",
      success: function(data) {
        $("#switchState").val(data.state);
      },
      error: function(jqXHR, textStatus, errorThrown) {
        alert("Error: " + errorThrown);
      }
    });
  });

  $("#moveSubmit").click(function() {
    $.ajax({
      method: "POST",
      url: "/v1/move",
      data: JSON.stringify({
        direction: $("#moveDirection").val(),
        speed: $("#moveSpeed").val(),
        duration: $("#moveDuration").val()
      }),
      contentType: "application/json; charset=UTF-8",
      error: function(jqXHR, textStatus, errorThrown) {
        alert("Error: " + errorThrown);
      }
    });
  });

  $("#motorsSubmit").click(function() {
    $.ajax({
      method: "POST",
      url: "/v1/motors",
      data: JSON.stringify({
        left_direction: $("#motorsLeftDirection").val(),
        left_speed: $("#motorsLeftSpeed").val(),
        right_direction: $("#motorsRightDirection").val(),
        right_speed: $("#motorsRightSpeed").val(),
      }),
      contentType: "application/json; charset=UTF-8",
      error: function(jqXHR, textStatus, errorThrown) {
        alert("Error: " + errorThrown);
      }
    });
  });

  $("#stopSubmit").click(function() {
    $.ajax({
      method: "POST",
      url: "/v1/stop",
      error: function(jqXHR, textStatus, errorThrown) {
        alert("Error: " + errorThrown);
      }
    });
  });

  $("#distanceSubmit").click(function() {
    $("#distanceValue").val("?");
    $.ajax({
      method: "GET",
      url: "/v1/distance",
      dataType: "json",
      success: function(data) {
        $("#distanceValue").val(data.distance);
      },
      error: function(jqXHR, textStatus, errorThrown) {
        alert("Error: " + errorThrown);
      }
    });
  });

});
