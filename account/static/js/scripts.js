/*!
    * Start Bootstrap - SB Admin v6.0.0 (https://startbootstrap.com/templates/sb-admin)
    * Copyright 2013-2020 Start Bootstrap
    * Licensed under MIT (https://github.com/BlackrockDigital/startbootstrap-sb-admin/blob/master/LICENSE)
    */
(function($) {
"use strict";
// Add active state to sidbar nav links
var path = window.location.href; // because the 'href' property of the DOM element is the absolute path
$("#layoutSidenav_nav .sb-sidenav a.nav-link").each(function() {
    if (this.href === path) {
        $(this).addClass("");
    }
});

// Toggle the side navigation
$("#sidebarToggle").on("click", function(e) {
    e.preventDefault();
    $("body").toggleClass("sb-sidenav-toggled");
});
})(jQuery);


//File Name populate
$(".custom-file-input").on("change", function() {
var fileName = $(this).val().split("\\").pop();
$(this).siblings(".custom-file-label").addClass("selected").html(fileName);
});



//var customer1= {{customer1|safe}}; Market Selection
var selectedCustomerName;
var selectedMarketname;
window.onload = function(){
    var option="<option value=''>--Select--</option>";
    for (var customer in customer1) { option = option + "<option value="+customer+">"+customer+"</option>" }
    document.getElementById("customer_nameSel").innerHTML= option;
}


function disableGrandChild(fieldToUpdate){
    var option="<option value=''>--Select--</option>";
    document.getElementById(fieldToUpdate).innerHTML= option;
}

function updateMarketNameOptions(value, fieldToUpdate) {
    document.getElementById(fieldToUpdate).removeAttribute("disabled");
    var customer = customer1[value];
    var option="<option value=''>--Select--</option>";
    for (var marketName in customer) { option = option + "<option value="+marketName+">"+marketName+"</option>" }
    document.getElementById(fieldToUpdate).innerHTML= option;
} 
function updateSoftwareRelOptions1(value, fieldToUpdate) {
    document.getElementById(fieldToUpdate).removeAttribute("disabled");
    var e=document.getElementById("customer_nameSel");
    var selectedCustName=e.options[e.selectedIndex].text;
    var market=customer1[selectedCustName][value];
    var option="<option value=''>--Select--</option>";
    for (var i=0; i < market.length; i ++) { option=option+"<option value="+market[i]+">"+market[i]+"</option>" }
    document.getElementById(fieldToUpdate).innerHTML= option;
}
function updateSoftwareRelOptions(value, fieldToUpdate) {
    document.getElementById(fieldToUpdate).removeAttribute("disabled");
    var e=document.getElementById("customer_nameSel");
    var selectedCustName=e.options[e.selectedIndex].text;
    var market=customer1[selectedCustName][value];
    var option="<option value=''>--Select--</option>";
    for (var software in market) { option = option + "<option value='"+software+"'>'"+software+"'</option>" }
    document.getElementById(fieldToUpdate).innerHTML= option;
}

function updateEnmRelOptions(value, fieldToUpdate) {
    document.getElementById(fieldToUpdate).removeAttribute("disabled");
    var customer=document.getElementById("customer_nameSel");
    var selectedCustName=customer.options[customer.selectedIndex].text;
    var market=document.getElementById("market_nameSel");
    var selectedMarket=market.options[market.selectedIndex].text;
    var software=customer1[selectedCustName][selectedMarket][value];
    console.log(software)
    console.log(value)
    var option="<option value=''>--Select--</option>";
    for (var enm in software) { option = option + "<option value="+enm+">"+enm+"</option>" }
    document.getElementById(fieldToUpdate).innerHTML= option;
}

function updateSoftwareRelOptionsNR(value, fieldToUpdate) {
    document.getElementById(fieldToUpdate).removeAttribute("disabled");
    var e=document.getElementById("customer_nameSel");
    var selectedCustName=e.options[e.selectedIndex].text;
    var market=customer1[selectedCustName][value];
    var option="<option value=''>--Select--</option>";
    for (var software in market) { option = option + "<option value="+software+">"+software+"</option>" }
    document.getElementById(fieldToUpdate).innerHTML= option;
}

