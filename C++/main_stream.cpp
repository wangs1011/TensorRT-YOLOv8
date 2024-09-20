#include <iostream>
#include <string>
#include "infer.h"
#include "BYTETracker.h"
#include <opencv2/core/utils/logger.hpp>


// 需要跟踪的类别，可以根据自己需求调整，筛选自己想要跟踪的对象的种类（以下对应COCO数据集类别索引）
std::vector<int>  trackClasses {0, 1, 2, 3, 5, 7};  // person, bicycle, car, motorcycle, bus, truck


bool isTrackingClass(int class_id){
	for (auto& c : trackClasses){
		if (class_id == c) return true;
	}
	return false;
}


int run(char* videoPath){
    // read video
    std::string inputVideoPath = std::string(videoPath);

    cv::utils::logging::setLogLevel(cv::utils::logging::LOG_LEVEL_DEBUG);


    cv::VideoCapture cap(inputVideoPath);

    if (!cap.isOpened()) {
        std::cerr << "Error: 视频无法打开" << std::endl;
        return -1;
    }

    int img_w = cap.get(CAP_PROP_FRAME_WIDTH);
	int img_h = cap.get(CAP_PROP_FRAME_HEIGHT);
    int fps = cap.get(CAP_PROP_FPS);
    long nFrame = static_cast<long>(cap.get(CAP_PROP_FRAME_COUNT));
    cout << "Total frames: " << nFrame << endl;

//    cv::VideoWriter writer("./result.mp4", VideoWriter::fourcc('m', 'p', '4', 'v'), fps, Size(img_w, img_h));

//    // YOLOv8 predictor
    std::string trtFile = "../detect/weights/yolov8s.trt";
    YoloDetector detector(trtFile, 0, 0.45, 0.01);
//    // ByteTrack tracker
//    BYTETracker tracker(fps, 30);
    std::cout << "Succeeded loading plan model!" << std::endl;

    cv::Mat img;
    int num_frames = 0;
    while (true){
        if ( !cap.read(img) ) break;
        num_frames++;
        if (img.empty()) break;
        if (num_frames % 20 == 0){
            cout << "Processing frame " << num_frames << endl;



            auto start = std::chrono::system_clock::now();

            std::vector<Detection> res = detector.inference(img);

            auto end = std::chrono::system_clock::now();
            int cost = std::chrono::duration_cast<std::chrono::milliseconds>(end - start).count();

            // draw result on image
            YoloDetector::draw_image(img, res);

            stringstream str;
            str << "../image_out/" << num_frames << ".jpg";        /*图片存储位置*/

            cout << str.str( ) << endl;
            imwrite( str.str( ), img );



        }


//         cv::imshow("img", img);
//         char c = waitKey(1);
//         if (c > 0) break;
    }

    cap.release();

    return 0;
}


int main(int argc, char* argv[]){
    if (argc != 2 )
    {
        std::cerr << "arguments not right!" << std::endl;
        std::cerr << "Usage: ./main [video path]" << std::endl;
        std::cerr << "Example: ./main ./videos/demo.mp4" << std::endl;
        return -1;
    }

    return run(argv[1]);
}
