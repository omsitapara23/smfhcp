$('#update-profile-form').on('submit', function(event){
    event.preventDefault();
    console.log("update profile form submitted!")
    updateProfile();
});

function csrfSafeMethod(method) {
    return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
}

function checkValidity() {
    $('#msgDivUpdateProfile').html('')
    $('#msgDivUpdateProfile').removeClass("alert alert-danger")
    if($('#txtPassword').val() == '' && $('#qualification').val() == '' && $('#profession').val() == '' &&
    $('#institution').val() == '' && $('#researchInterests').val() == '' && $('#clinicalInterests').val() == '') {
        $('#msgDivUpdateProfile').addClass("alert alert-danger").html("All fields are empty.");
        console.log("All fields empty");
        return false;
    }
    return true;
}

function updateProfile() {
    var csrftoken = jQuery("[name=csrfmiddlewaretoken]").val();
    var qualifications = []
    var researchInterests = []
    var clinicalInterests = []
    $('input[name="qualification[]"]').each(function() {
        if ($(this).val() != '') {
            qualifications.push($(this).val());
        }
    });
    $('input[name="researchInterests[]"]').each(function() {
        if ($(this).val() != '') {
            researchInterests.push($(this).val());
        }
    });
    $('input[name="clinicalInterests[]"]').each(function() {
        if ($(this).val() != '') {
            clinicalInterests.push($(this).val());
        }
    });
    if(checkValidity()) {
        $.ajax({
            url : "/update_profile/",
            type : "POST",
            data : { password : $('#txtPassword').val(), qualification : JSON.stringify({ 'qualifications': qualifications }), profession : $('#profession').val(),
            institution : $('#institution').val(), researchInterests : JSON.stringify({ 'researchInterests': researchInterests }),
            clinicalInterests : JSON.stringify({ 'clinicalInterests': clinicalInterests }) },
            beforeSend: function(xhr, settings) {
                if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
                    xhr.setRequestHeader("X-CSRFToken", csrftoken);
                }
            },
            success : function(json) {
                if (json.redirect) {
                    window.location.href = json.redirect_url;
                } else {
                    console.log('failed to redirect')
                }
            },
            error : function(xhr,errmsg,err) {
                console.log(xhr.status + ": " + xhr.responseText);
            }
        });
    }
}

$("#qualAddButton").click(function(){
    $("#qualWrapper").append("<div class=\"input-group\" style=\"margin-top: 10px;\">" +
                    "<input name=\"qualification[]\" type=\"text\" required=\"true\" class=\"form-control\">" +
                    "<span class=\"input-group-btn\">" +
                        "<button class=\"btn btn-success btn-remove plus-minus\" type=\"button\">" +
                            "<i class=\"fa fa-minus\"></i>" +
                        "</button>" +
                    "</span>" +
                "</div>");
});

$("#researchIntAddButton").click(function(){
    $("#researchIntWrapper").append("<div class=\"input-group\" style=\"margin-top: 10px;\">" +
                    "<input name=\"researchInterests[]\" type=\"text\" required=\"true\" class=\"form-control\">" +
                    "<span class=\"input-group-btn\">" +
                        "<button class=\"btn btn-success btn-remove plus-minus\" type=\"button\">" +
                            "<i class=\"fa fa-minus\"></i>" +
                        "</button>" +
                    "</span>" +
                "</div>");
});

$("#clinicalIntAddButton").click(function(){
    $("#clinicalIntWrapper").append("<div class=\"input-group\" style=\"margin-top: 10px;\">" +
                    "<input name=\"clinicalInterests[]\" type=\"text\" required=\"true\" class=\"form-control\">" +
                    "<span class=\"input-group-btn\">" +
                        "<button class=\"btn btn-success btn-remove plus-minus\" type=\"button\">" +
                            "<i class=\"fa fa-minus\"></i>" +
                        "</button>" +
                    "</span>" +
                "</div>");
});

$(document).ready(function() {
    $(document).on("click",".btn-remove", function(e){
		e.preventDefault();
		 $(this).parents('.input-group:first').remove();
	})
}
);