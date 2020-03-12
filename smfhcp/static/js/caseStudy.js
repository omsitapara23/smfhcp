$("#caseStudyTagsAddButton").click(function(){
    $("#caseStudyTagsWrapper").append("<div class=\"input-group\" style=\"margin-top: 10px;\">" +
                    "<input name=\"tags[]\" type=\"text\" required=\"true\" class=\"form-control\">" +
                    "<span class=\"input-group-btn\">" +
                        "<button class=\"btn btn-success btn-remove plus-minus\" type=\"button\">" +
                            "<i class=\"fa fa-minus\"></i>" +
                        "</button>" +
                    "</span>" +
                "</div>");
});

$("#case-study-form").on('submit', function(event){
    event.preventDefault();
    console.log("case study form submitted!")
    caseStudy();
});

function caseStudy() {
    var csrftoken = jQuery("[name=csrfmiddlewaretoken]").val();
    var tags = []
    $('input[name="tags[]"]').each(function() {
        tags.push($(this).val());
    });
    $.ajax({
        url : "/create_post/case_study/",
        type : "POST",
        data : { title : $('#caseStudyTitle').val(), history : $('#caseStudyHistory').val(),
            examination : $('#caseStudyExamination').val(), diagnosis: $('#caseStudyDiagnosis').val(), treatment : $('#caseStudyTreatment').val(),
            prevention : $('#caseStudyPrevention').val(), tags : JSON.stringify({ 'tags': tags }),
            remarks : $('#caseStudyRemarks').val()
        },
        beforeSend: function(xhr, settings) {
            if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
                xhr.setRequestHeader("X-CSRFToken", csrftoken);
            }
        },
        success : function(json) {
            if (json.redirect) {
                window.location.href = json.redirect_url;
            }
        },
        error : function(xhr,errmsg,err) {
            console.log(xhr.status + ": " + xhr.responseText);
        }
    });
}
