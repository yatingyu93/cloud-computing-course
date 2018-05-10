function invoke_search(sdk_search, kw) {
    return sdk_search.moviebotPost({}, {
        "f": "search",
        "keyword": kw
    }, {});
}

function search(sdk_search, kw) {
    // Returning the promise
    return invoke_search(sdk_search, kw).then( function(response) {
        console.log(response.data);
        return response.data;
    });
}


/*------------------------- ---Initial--------------------------------*/
var pre_url = "./home.html?mid="
var cur = 0;
/*-----------------------------Script---------------------------------*/

$( document ).ready(function() {

    // cognito authentication
    var sdk_search = {};
    AWS.config.region = 'us-east-1';
    AmazonCognitoIdentity.region = 'us-east-1';
    var poolData = {
        UserPoolId: 'us-east-1_jDv7ZZJB9',
        ClientId: '2najgqvdlpscumkfl2r5smpi3k'
    };
    var userPool = new AmazonCognitoIdentity.CognitoUserPool(poolData);
    var logout_url = "https://cc-pj-domain.auth.us-east-1.amazoncognito.com/logout?client_id=2najgqvdlpscumkfl2r5smpi3k&logout_uri=https://s3.amazonaws.com/cloud-computing-project-bucket/frontend/index.html";
    $("#logout").attr('href', logout_url);
    var cognitoUser = userPool.getCurrentUser();
    if (cognitoUser != null) {
        cognitoUser.getSession(function (err, session) {
            if (err) {
                alert(err);
                return;
            }
            console.log(session);
            cognitoUser.getUserAttributes(function(err, result) {
                if (err) {
                    alert(err);
                    return;
                }
                for (var i = 0; i < result.length; i++) {
                    if (result[i].getName() == 'name' || result[i].getName() == 'email') {
                        console.log(result[i].getValue());
                    }
                }
            });
            console.log('session validity: ' + session.isValid());

            sdk_search = apigClientFactoryM.newClient();
        });
    } else {
        alert("login please");
        window.location = "./index.html";
    }
    $("#logout").click(function () {
        cognitoUser.signOut();
    });


    /*-------------------------------Data----------------------------------*/
    // search api
    var url = new URL(window.location.href);
    var kw = url.searchParams.get("keyword");
    $('#keyword').val(kw);

    var movielist = [];
    var searchres = search(sdk_search, kw);
    var mid=[], title=[], poster=[], rating=[], release_date=[], overview=[], genres=[];
    var msize = 0;
    // Wait for search promise to finish
    $.when(searchres).done(function (rsp) {
        $('#loading').hide();
        $('.container').show();
        msize = rsp.length;
        console.log(msize);
        console.log('data loaded: ' + msize);
        movielist = rsp;
        for (var i = 0; i < msize; i++) {
            mid.push(rsp[i]['mid']);
            title.push(rsp[i]['title']);
            poster.push(rsp[i]['poster']);
            rating.push(rsp[i]['rating']);
            release_date.push(rsp[i]['release_date']);
            overview.push(rsp[i]['overview']);
            genres.push(rsp[i]['genres']);
        }

        appendRow(msize, cur, mid, poster,title,rating);
        cur = Math.min(cur+4,msize);
        appendRow(msize, cur, mid, poster,title,rating);
        cur = Math.min(cur+4,msize);

    });

    /*-----------------------------eki-----------------------------*/


    $(window).scroll(function(event){
        if($(window).scrollTop() + $(window).height() >= $(document).height()) {
          appendRow(msize, cur, mid, poster,title,rating);
          cur = Math.min(cur+4,msize);
        }
    });

    $('body').on('mouseenter', 'a', function() {
      var hoverid = urlParse(this.href,"mid");
      if(hoverid != null) {
        var topPos = this.offsetTop;
        var leftPos = this.offsetLeft;
        renewPop(hoverid,topPos,leftPos, mid,title, rating, genres, overview, release_date);
      }
    });

    $('body').on('mouseleave', 'a', function() {
      var hoverid = urlParse(this.href,"mid");
      if(hoverid != null) {
        $(".detail-pop").css({"display":"none"});
      }
    });

});


/* extract parameters from url
eg.string "123"=urlParse("http://example.com/kid=123",kid)*/
function urlParse(targetUrl,key) {
  var regExp = new RegExp('([?]|&)' + key + '=([^&]*)(&|$)');
    var result = targetUrl.match(regExp);
    if (result) {
        return decodeURIComponent(result[2]);
    } else {
        return null;
    }
}

/*Need global vars:
detail_page_url = pre_url | starting_index = offset| movie_id_list = mid[] | movie_poster_list = poster[] | movie_name_list = title[] | movie_rating_list = rating[]
 Add a row containing 4 movie-block from offset in movie list*/
function appendRow(msize, offset, mid, poster,title,rating) {
   var newRow = "<div class='movie-block-row'> ";
   for(var i = 0; i < 4 && i+offset < msize; i++) {
     newRow += "<a class='movie-block-cover' href = '"+pre_url+mid[offset+i]+"'><div class='movie-block'><img class='img-movie-block' src='"
         + poster[offset+i]+"'><div class='detail-movie-block'><p>"+title[offset+i]+"  <strong>"+rating[offset+i]+"</strong></p></div></div></a>";
   }
   newRow += "</div>";
   $( ".container" ).append(newRow);
}

/*Need global vars:
detail_page_url=pre_url|movie_id_list=mid[]|movie_name_list title[]|movie_rating_list=rating[]|movie_genras=genre[]|movie_overview_list=overview[]
input: movie_id=hoverid|position=(topPos,leftPos)
Output:when the pointer enters movie-block, display coresponding detail-pop element*/
function renewPop(hoverid,topPos,leftPos, mid, title, rating, genre, overview, release_date){
  var idx = mid.indexOf(hoverid);
  $(".detail-pop").empty();
  var year = "????";
  if(release_date[idx] != null) year = release_date[idx].substring(0,4);
  var newdetail = "<h3><a href='"+pre_url+hoverid+"'>"+title[idx]+" ("+year+")</a></h3><div class='detail'><span>Rating: </span> <strong>"+
      rating[idx]+"</strong></div><div class='detail'><span>Genres: </span>"+genre[idx]+"</div><div class='detail'><span>Overview: </span>"
      +overview[idx]+"</div></div>";
  $(".detail-pop").append(newdetail);
  if(idx % 4 < 2) {
    leftPos += 250;
  } else {
    leftPos -=300;
  }
  $(".detail-pop").css({"top":topPos,"left":leftPos,"display":"inline"});
}
