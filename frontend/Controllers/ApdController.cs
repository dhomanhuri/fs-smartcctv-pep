using System;
using System.Linq;
using System.Web.Mvc;
using MvcSmartCctv.Models;
using MvcSmartCctv.Services;

namespace MvcSmartCctv.Controllers
{
    public class ApdController : BaseController
    {
        public ActionResult Index()
        {
            SetShell("apd");
            ViewBag.Title = "APD Detection";

            var token = CurrentUser.AccessToken;
            var cameras = FastApiClient.GetCameras("apd", token);
            var violations = FastApiClient.GetViolations("apd", 100, token);
            var since24h = DateTime.Now.AddHours(-24);

            var vm = new DetectionViewModel
            {
                Category = "apd",
                PageTitle = "APD Detection",
                PageDescription = "Deteksi kepatuhan alat pelindung diri (mis. helm) di kamera terkait.",
                AccentColor = "#B57712",
                Cameras = cameras,
                Violations = violations,
                StatCams = cameras.Count,
                StatToday = violations.Count(v => v.CreatedAt >= since24h),
                StatOpen = violations.Count(v => v.IsCase && v.Status != "selesai"),
            };
            return View("~/Views/Shared/Detection.cshtml", vm);
        }
    }
}
