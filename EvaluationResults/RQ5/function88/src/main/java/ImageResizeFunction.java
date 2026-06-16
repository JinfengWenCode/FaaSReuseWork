```java
import com.google.gson.JsonObject;
import org.apache.commons.codec.binary.Base64;
import javax.imageio.ImageIO;
import java.awt.*;
import java.awt.image.BufferedImage;
import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.io.IOException;

public class ImageResizeFunction {

    public static JsonObject main(JsonObject args) {
        JsonObject response = new JsonObject();

        try {
            // Extract input parameters
            String base64Image = args.getAsJsonPrimitive("image").getAsString();
            int newWidth = args.getAsJsonPrimitive("width").getAsInt();
            int newHeight = args.getAsJsonPrimitive("height").getAsInt();

            // Decode the base64 image
            byte[] imageBytes = Base64.decodeBase64(base64Image);
            ByteArrayInputStream inputStream = new ByteArrayInputStream(imageBytes);
            BufferedImage originalImage = ImageIO.read(inputStream);

            // Resize the image
            Image resizedImage = originalImage.getScaledInstance(newWidth, newHeight, Image.SCALE_SMOOTH);
            BufferedImage bufferedResizedImage = new BufferedImage(newWidth, newHeight, originalImage.getType());

            Graphics2D g2d = bufferedResizedImage.createGraphics();
            g2d.drawImage(resizedImage, 0, 0, null);
            g2d.dispose();

            // Encode the resized image to base64
            ByteArrayOutputStream outputStream = new ByteArrayOutputStream();
            ImageIO.write(bufferedResizedImage, "jpg", outputStream);
            byte[] resizedImageBytes = outputStream.toByteArray();
            String base64ResizedImage = Base64.encodeBase64String(resizedImageBytes);

            // Prepare the response
            response.addProperty("resizedImage", base64ResizedImage);
        } catch (IOException e) {
            response.addProperty("error", "Failed to process the image: " + e.getMessage());
        } catch (Exception e) {
            response.addProperty("error", "An error occurred: " + e.getMessage());
        }

        return response;
    }
}
```